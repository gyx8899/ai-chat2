"""LLM 配置管理路由。

重构后使用新模块路径。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.core.constants import APIStatus, ProviderConstants
from app.core.settings import get_settings, LLMProvider
from app.db.schemas import LLMConfig
from app.integrations import build_model_list, get_model_by_id

router = APIRouter()


@router.get("/")
async def get_config() -> dict:
    """获取当前 LLM 配置和可用模型列表。"""
    settings = get_settings()
    models = await build_model_list()

    return {
        "provider": settings.llm.provider.value,
        "model": settings.llm.model,
        "api_base": settings.llm.api_base,
        "available_providers": [p.value for p in LLMProvider],
        "models": models,
    }


@router.post("/")
async def update_config(config: LLMConfig) -> dict:
    """更新 LLM 配置。"""
    settings = get_settings()

    # 验证 provider
    valid_providers = [p.value for p in LLMProvider]
    if config.provider not in valid_providers:
        raise HTTPException(
            status_code=APIStatus.BAD_REQUEST,
            detail=f"Invalid provider: {config.provider}",
        )

    # 如果指定了模型，验证模型 ID 是否存在于可用列表中
    # 注意：允许使用不在硬编码列表中的模型（如 Ollama 本地模型）
    # 但云端模型的 provider 应该与模型定义一致
    if config.model is not None:
        models = await build_model_list()
        model = get_model_by_id(config.model, models)
        if model is not None and model["provider"] != config.provider:
            raise HTTPException(
                status_code=APIStatus.BAD_REQUEST,
                detail=f"Model {config.model} is not a {config.provider} model",
            )

    # 更新配置（实际生产中应持久化）
    settings.llm.provider = LLMProvider(config.provider)
    if config.model is not None:
        settings.llm.model = config.model
    if config.api_base is not None:
        settings.llm.api_base = config.api_base
    if config.api_key is not None:
        settings.llm.api_key = config.api_key

    return {
        "status": "ok",
        "provider": config.provider,
        "model": settings.llm.model,
    }


@router.get("/llm")
async def get_llm_config() -> dict:
    """获取当前 LLM 配置（别名）。"""
    settings = get_settings()
    return {
        "provider": settings.llm.provider.value,
        "model": settings.llm.model,
        "api_base": settings.llm.api_base,
    }


@router.post("/llm")
async def update_llm_config(config: LLMConfig) -> dict:
    """更新 LLM 配置（别名）。"""
    settings = get_settings()

    # 验证 provider
    valid_providers = [p.value for p in LLMProvider]
    if config.provider not in valid_providers:
        raise HTTPException(
            status_code=APIStatus.BAD_REQUEST,
            detail=f"Invalid provider: {config.provider}",
        )

    # 更新配置（实际生产中应持久化）
    settings.llm.provider = LLMProvider(config.provider)
    if config.model is not None:
        settings.llm.model = config.model
    if config.api_base is not None:
        settings.llm.api_base = config.api_base
    if config.api_key is not None:
        settings.llm.api_key = config.api_key

    return {"message": "LLM config updated", "provider": config.provider}


@router.get("/providers")
async def get_providers() -> dict:
    """获取支持的 LLM Provider 列表。"""
    return {
        "providers": [
            {"name": p.value, "description": _get_provider_desc(p.value)}
            for p in LLMProvider
        ]
    }


@router.get("/models")
async def get_models() -> dict:
    """获取可用模型列表（含动态发现的 Ollama 模型）。"""
    models = await build_model_list()
    return {"models": models}


def _get_provider_desc(provider: str) -> str:
    """获取 Provider 描述。"""
    desc_map = {
        ProviderConstants.MOCK: "Mock provider for testing",
        ProviderConstants.OPENAI: "OpenAI API (GPT series)",
        ProviderConstants.OLLAMA: "Ollama local models",
    }
    return desc_map.get(provider, "Unknown provider")