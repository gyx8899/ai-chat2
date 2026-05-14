"""Domain LLM 模块 - LLM 服务。

采用策略模式 + 工厂模式，支持运行时注册新 Provider。
"""

import json
import time
from typing import AsyncGenerator, Optional, Union

from app.core.settings import get_settings
from app.core.exceptions import AppException, ErrorCode
from app.observability.logging import get_logger
from app.observability.metrics import (
    llm_request_duration_seconds,
    llm_requests_total,
)
from app.reliability import get_circuit_breaker
from app.domain.llm.providers.base import (
    get_provider_registry,
    LLMResponse,
)
from app.domain.llm.providers import MockProvider  # noqa: F401 - 触发注册

logger = get_logger(__name__)


def get_current_llm_config() -> dict:
    """获取当前 LLM 配置（支持热更新）。"""
    s = get_settings()
    return {
        "provider": s.llm.provider.value,
        "model": s.llm.model,
        "api_base": s.llm.api_base,
        "api_key": s.llm.api_key,
    }


async def chat_stream(
    messages: list[dict[str, str]],
    session_id: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """流式对话生成器（仅返回 token，由上层组装 SSE 帧）。

    集成可靠性治理：
    - 熔断器保护
    - 超时控制
    - 指标采集

    Args:
        messages: 消息历史
        session_id: 可选会话 ID
        model: 可选模型 ID，覆盖全局配置

    Yields:
        Token 字符串
    """
    config = get_current_llm_config()
    registry = get_provider_registry()

    # 统一转换 provider 为字符串
    provider = config.get("provider", "mock")
    if hasattr(provider, "value"):
        provider = provider.value

    # 根据模型 ID 推断 provider（优先级：请求模型 > 全局配置）
    if model:
        inferred_provider = registry.resolve_provider(model)
        provider = inferred_provider

    provider_obj = registry.get(provider)
    if not provider_obj:
        logger.error("llm_provider_not_found", provider=provider)
        raise AppException(
            ErrorCode.LLM_API_ERROR,
            f"Provider '{provider}' not found",
        )

    start = time.perf_counter()
    status = "success"

    try:
        # 通过熔断器调用（mock 不需要熔断）
        if provider == "mock":
            async for frame in provider_obj.stream(messages, model):
                if frame.error:
                    raise AppException(ErrorCode.LLM_API_ERROR, frame.error)
                if frame.content:
                    yield frame.content
        else:
            breaker = get_circuit_breaker(f"llm_{provider}")
            gen = _stream_with_provider(provider_obj, model, messages)

            # 熔断器只保护"启动"阶段
            async def _start_stream():
                return gen

            protected_gen = await breaker.call(_start_stream)
            async for frame in protected_gen:
                if frame.error:
                    raise AppException(ErrorCode.LLM_API_ERROR, frame.error)
                if frame.content:
                    yield frame.content

    except AppException as e:
        status = (
            "error"
            if e.code == ErrorCode.LLM_API_ERROR
            else "timeout"
            if e.code == ErrorCode.LLM_TIMEOUT
            else "circuit_open"
        )
        logger.error(
            "llm_request_failed",
            provider=provider,
            error_code=e.code.value,
            error_message=e.message,
        )
        raise
    except Exception as e:
        status = "error"
        logger.error(
            "llm_request_unexpected_error",
            provider=provider,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise AppException(
            ErrorCode.LLM_API_ERROR,
            f"Unexpected error: {e}",
        )
    finally:
        duration = time.perf_counter() - start
        llm_requests_total.labels(provider=provider, status=status).inc()
        llm_request_duration_seconds.labels(provider=provider).observe(duration)


async def _stream_with_provider(
    provider,
    model: Optional[str],
    messages: list[dict[str, str]],
) -> AsyncGenerator[LLMResponse, None]:
    """包装 Provider 流式输出，转换为 LLMResponse。"""
    async for frame in provider.stream(messages, model):
        yield frame


# ============================================================================
# SSE 帧工具函数（对齐原项目协议）
# ============================================================================


def format_content_frame(content: str) -> str:
    """内容帧: `data: {"content":"x"}\n\n`"""
    return f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"


def format_error_frame(message: str) -> str:
    """错误帧: `data: {"error":"x"}\n\n`"""
    return f"data: {json.dumps({'error': message}, ensure_ascii=False)}\n\n"


def format_meta_frame(meta: dict) -> str:
    """元数据帧: `data: {"meta":{...}}\n\n`"""
    return f"data: {json.dumps({'meta': meta}, ensure_ascii=False)}\n\n"


def format_done_frame() -> str:
    """结束帧: `data: [DONE]\n\n`"""
    return "data: [DONE]\n\n"


def format_heartbeat_frame() -> str:
    """SSE 心跳帧（注释行）。"""
    return ": heartbeat\n\n"


__all__ = [
    "chat_stream",
    "get_current_llm_config",
    "format_content_frame",
    "format_error_frame",
    "format_meta_frame",
    "format_done_frame",
    "format_heartbeat_frame",
]