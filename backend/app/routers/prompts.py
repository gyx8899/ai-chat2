"""提示词配置 API 路由。"""

from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.prompts.service import get_prompt_service
from app.core.settings import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class PromptListResponse(BaseModel):
    """提示词列表响应（不含 content/variables）。"""

    prompts: list[dict]
    default_type: str
    categories: list[dict]


class ReloadResponse(BaseModel):
    """Reload 响应。"""

    status: str
    count: int


async def _notify_frontend_revalidate() -> None:
    """通知前端重新验证 prompts 缓存。"""
    settings = get_settings()
    frontend_url = settings.prompts.frontend_url
    revalidate_secret = settings.prompts.revalidate_secret

    if not frontend_url or not revalidate_secret:
        logger.warning("revalidate_skipped_missing_config")
        return

    url = f"{frontend_url}/api/revalidate-prompts?secret={revalidate_secret}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            logger.info("revalidate_notified", status=response.status_code, url=url)
    except httpx.HTTPStatusError as e:
        logger.warning("revalidate_failed", error=str(e), status=e.response.status_code)
    except Exception as e:
        logger.warning("revalidate_failed", error=str(e))


@router.get("/", response_model=PromptListResponse)
async def list_prompts() -> PromptListResponse:
    """获取所有提示词列表（不含 content/variables）。"""
    service = get_prompt_service()
    infos = service.list_info()
    categories = service.categories()

    return PromptListResponse(
        prompts=[p.model_dump() for p in infos],
        default_type=service.default_type(),
        categories=[{"id": c.value, "name": c.value} for c in categories],
    )


@router.get("/list")
async def list_prompts_for_frontend() -> dict:
    """供前端 RSC 调用的提示词列表接口。

    返回格式与前端 PromptListItem 完全对齐：
    {data: PromptListItem[]}
    """
    service = get_prompt_service()
    infos = service.list_info()

    # examples 已在 Schema 层定义为 list[str]，直接序列化
    return {"data": [p.model_dump() for p in infos]}


@router.get("/{type_id}")
async def get_prompt(type_id: str) -> dict:
    """获取指定提示词详情（含 content，仅内部使用）。"""
    service = get_prompt_service()
    prompt = service.get_prompt(type_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail=f"Prompt '{type_id}' not found")
    return prompt.model_dump()


@router.post("/reload", response_model=ReloadResponse)
async def reload_prompts(
    secret: Optional[str] = Query(default=None),
) -> ReloadResponse:
    """重新加载提示词配置并触发前端缓存失效。

    必须提供正确的 reload_secret（通过 ?secret= 查询参数）。
    """
    settings = get_settings()
    expected = settings.prompts.reload_secret

    if not expected or secret != expected:
        logger.warning("reload_unauthorized", provided_secret=secret)
        raise HTTPException(status_code=401, detail="invalid reload secret")

    service = get_prompt_service()
    count = await service.reload()

    # 触发前端缓存失效
    await _notify_frontend_revalidate()

    logger.info("reload_success", count=count)
    return ReloadResponse(status="ok", count=count)