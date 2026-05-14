"""Observability 模块 - 可观测性基础设施。

提供结构化日志和 Prometheus 指标。
采用 DDD 分层架构。
"""

from app.observability.logging import (
    configure_logging,
    get_logger,
    bind_trace_id,
    clear_context,
)
from app.observability.metrics import (
    MetricsMiddleware,
    http_requests_total,
    http_request_duration_seconds,
    sse_active_connections,
    sse_connection_duration_seconds,
    llm_requests_total,
    llm_request_duration_seconds,
    llm_tokens_total,
    get_metrics_response,
)

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    "bind_trace_id",
    "clear_context",
    # Metrics
    "MetricsMiddleware",
    "http_requests_total",
    "http_request_duration_seconds",
    "sse_active_connections",
    "sse_connection_duration_seconds",
    "llm_requests_total",
    "llm_request_duration_seconds",
    "llm_tokens_total",
    "get_metrics_response",
]