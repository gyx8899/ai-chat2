"""Observability 模块 - Prometheus 指标。

重构自 app/metrics.py - 采用 DDD 分层架构。
符合 R3.4 可观测性需求。
"""

import re
import time
from typing import Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ============================================================================
# HTTP 指标
# ============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "HTTP 请求总数",
    labelnames=["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP 请求耗时（秒）",
    labelnames=["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ============================================================================
# SSE 指标
# ============================================================================

sse_active_connections = Gauge(
    "sse_active_connections",
    "当前活跃 SSE 连接数",
)

sse_connection_duration_seconds = Histogram(
    "sse_connection_duration_seconds",
    "SSE 连接持续时长（秒）",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800),
)

# ============================================================================
# LLM 指标
# ============================================================================

llm_requests_total = Counter(
    "llm_requests_total",
    "LLM 调用总数",
    labelnames=["provider", "status"],  # status: success/timeout/error/circuit_open
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM 调用耗时（秒）",
    labelnames=["provider"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "LLM token 消耗量",
    labelnames=["provider", "direction"],  # direction: input/output
)


# ============================================================================
# FastAPI 中间件
# ============================================================================


class MetricsMiddleware(BaseHTTPMiddleware):
    """请求级指标采集中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录请求耗时和状态。"""
        # 排除 /metrics 端点自身
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            duration = time.perf_counter() - start
            path = _normalize_path(request.url.path)
            http_requests_total.labels(
                method=request.method,
                path=path,
                status=status,
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                path=path,
            ).observe(duration)

        return response


def _normalize_path(path: str) -> str:
    """归一化路径（去除 ID 等动态部分），避免指标基数爆炸。

    /api/v1/sessions/abc-123/messages → /api/v1/sessions/:id/messages
    """
    # UUID 模式
    path = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "/:id",
        path,
    )
    # 数字 ID
    path = re.sub(r"/\d+", "/:id", path)
    return path


def get_metrics_response() -> Response:
    """返回 Prometheus 格式的指标响应。"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


__all__ = [
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