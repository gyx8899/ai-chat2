"""Core 模块 - 应用核心异常与错误处理。

重构自 app/errors.py - 采用 DDD 分层架构。

设计原则：
- 业务错误码采用 ABCD 格式（4 位整数）
  - A: 模块（1-LLM, 2-Session, 3-Config, 4-Auth, 9-System）
  - BCD: 错误编号（001-999）
- HTTP 状态码用于传输层
- 错误码 + 错误消息分层：错误码用于程序判断，消息用于用户展示
"""

from enum import IntEnum
from typing import Any, Optional

from fastapi import HTTPException


class ErrorCode(IntEnum):
    """业务错误码。"""

    # 通用错误 (9xxx)
    UNKNOWN_ERROR = 9000
    INTERNAL_ERROR = 9001
    INVALID_PARAMS = 9002
    NOT_FOUND = 9003

    # LLM 错误 (1xxx)
    LLM_TIMEOUT = 1001
    LLM_API_ERROR = 1002
    LLM_RATE_LIMITED = 1003
    LLM_CIRCUIT_OPEN = 1004
    LLM_PROVIDER_UNAVAILABLE = 1005
    LLM_INVALID_CONFIG = 1006

    # Session 错误 (2xxx)
    SESSION_NOT_FOUND = 2001
    SESSION_INVALID_ID = 2002
    SESSION_TITLE_TOO_LONG = 2003
    MESSAGE_TOO_LONG = 2004

    # Config 错误 (3xxx)
    CONFIG_INVALID_PROVIDER = 3001
    CONFIG_MISSING_API_KEY = 3002
    CONFIG_INVALID_MODEL = 3003


# 错误码 → HTTP 状态码映射
ERROR_TO_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.INVALID_PARAMS: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.LLM_TIMEOUT: 504,
    ErrorCode.LLM_API_ERROR: 502,
    ErrorCode.LLM_RATE_LIMITED: 429,
    ErrorCode.LLM_CIRCUIT_OPEN: 503,
    ErrorCode.LLM_PROVIDER_UNAVAILABLE: 503,
    ErrorCode.LLM_INVALID_CONFIG: 400,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.SESSION_INVALID_ID: 400,
    ErrorCode.SESSION_TITLE_TOO_LONG: 400,
    ErrorCode.MESSAGE_TOO_LONG: 400,
    ErrorCode.CONFIG_INVALID_PROVIDER: 400,
    ErrorCode.CONFIG_MISSING_API_KEY: 400,
    ErrorCode.CONFIG_INVALID_MODEL: 400,
}


class AppException(Exception):
    """应用统一异常基类。

    用法：
        raise AppException(ErrorCode.LLM_TIMEOUT, "OpenAI request timeout")
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    @property
    def http_status(self) -> int:
        """对应的 HTTP 状态码。"""
        return ERROR_TO_HTTP_STATUS.get(self.code, 500)

    def to_dict(self) -> dict[str, Any]:
        """转换为 JSON 响应格式。"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }

    def to_http_exception(self) -> HTTPException:
        """转换为 FastAPI HTTPException。"""
        return HTTPException(
            status_code=self.http_status,
            detail=self.to_dict(),
        )


def raise_app_error(
    code: ErrorCode,
    message: str,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """快捷抛出 HTTPException（带统一错误码）。"""
    raise AppException(code, message, details).to_http_exception()


# 向后兼容别名
__all__ = [
    "ErrorCode",
    "ERROR_TO_HTTP_STATUS",
    "AppException",
    "raise_app_error",
]