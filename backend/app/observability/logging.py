"""Observability 模块 - 结构化日志配置。

重构自 app/logging_config.py - 采用 DDD 分层架构。
使用 structlog 进行结构化日志记录。
"""

import logging
import sys

import structlog

from app.core.settings import get_settings


def configure_logging() -> None:
    """配置全局日志。

    根据环境（debug 模式）选择输出格式：
    - debug=True: ConsoleRenderer（彩色，可读）
    - debug=False: JSONRenderer（结构化）
    """
    settings = get_settings()

    # 标准 logging 模块配置
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.api.debug else logging.INFO,
    )

    # 共享处理器
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,  # 合并 contextvars
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # 根据环境选择 renderer
    if settings.api.debug:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """获取 structlog logger。

    用法：
        log = get_logger(__name__)
        log.info("user_login", user_id=123, duration_ms=42)
    """
    return structlog.get_logger(name)


def bind_trace_id(trace_id: str) -> None:
    """绑定 trace_id 到当前上下文（贯穿整个请求）。"""
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_context() -> None:
    """清除上下文（请求结束时调用）。"""
    structlog.contextvars.clear_contextvars()


__all__ = [
    "configure_logging",
    "get_logger",
    "bind_trace_id",
    "clear_context",
]