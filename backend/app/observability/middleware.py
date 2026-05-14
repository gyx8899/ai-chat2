"""Observability 模块 - 中间件。

重构自 app/middleware.py - TraceId 和请求日志中间件。
"""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.logging import bind_trace_id, clear_context, get_logger

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """生成/提取 trace_id 并注入到日志上下文。

    客户端可通过 `X-Trace-Id` 头传递自定义 trace_id，
    否则服务端自动生成 UUID。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求。"""
        # 提取或生成 trace_id
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex[:16]

        # 绑定到 structlog 上下文
        bind_trace_id(trace_id)

        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            # 在响应头回传 trace_id 便于客户端关联
            response.headers["X-Trace-Id"] = trace_id
            return response
        except Exception as e:
            logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status=status_code,
                duration_ms=round(duration_ms, 2),
            )
            clear_context()


__all__ = ["TraceIdMiddleware"]