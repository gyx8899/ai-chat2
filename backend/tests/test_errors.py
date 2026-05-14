"""错误码体系测试。"""

import pytest
from fastapi import HTTPException

from app.core.exceptions import AppException, ErrorCode, raise_app_error


class TestErrorCode:
    """错误码枚举测试。"""

    def test_error_code_values(self) -> None:
        """错误码按模块分组。"""
        # 通用错误 9xxx
        assert ErrorCode.UNKNOWN_ERROR.value == 9000
        assert ErrorCode.INVALID_PARAMS.value == 9002

        # LLM 错误 1xxx
        assert ErrorCode.LLM_TIMEOUT.value == 1001
        assert ErrorCode.LLM_CIRCUIT_OPEN.value == 1004

        # Session 错误 2xxx
        assert ErrorCode.SESSION_NOT_FOUND.value == 2001


class TestAppException:
    """应用异常基类测试。"""

    def test_app_exception_basic(self) -> None:
        """基础异常构造。"""
        exc = AppException(ErrorCode.LLM_TIMEOUT, "timeout")
        assert exc.code == ErrorCode.LLM_TIMEOUT
        assert exc.message == "timeout"
        assert exc.details == {}

    def test_app_exception_http_status(self) -> None:
        """HTTP 状态码映射。"""
        exc = AppException(ErrorCode.LLM_TIMEOUT, "timeout")
        assert exc.http_status == 504  # Gateway Timeout

        exc = AppException(ErrorCode.SESSION_NOT_FOUND, "not found")
        assert exc.http_status == 404

        exc = AppException(ErrorCode.LLM_CIRCUIT_OPEN, "circuit open")
        assert exc.http_status == 503

    def test_to_dict(self) -> None:
        """转换为 JSON 响应格式。"""
        exc = AppException(
            ErrorCode.INVALID_PARAMS,
            "bad request",
            details={"field": "query"},
        )
        d = exc.to_dict()
        assert d == {
            "code": 9002,
            "message": "bad request",
            "details": {"field": "query"},
        }

    def test_to_http_exception(self) -> None:
        """转换为 FastAPI HTTPException。"""
        exc = AppException(ErrorCode.SESSION_NOT_FOUND, "not found")
        http_exc = exc.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404

    def test_raise_app_error(self) -> None:
        """快捷抛出函数。"""
        with pytest.raises(HTTPException) as exc_info:
            raise_app_error(ErrorCode.LLM_TIMEOUT, "timeout")
        assert exc_info.value.status_code == 504