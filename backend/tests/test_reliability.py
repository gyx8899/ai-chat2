"""可靠性治理测试 - 超时/重试/熔断。"""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppException, ErrorCode
from app.reliability import (
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker,
    reset_circuit_breakers,
    retry_async,
    with_timeout,
)


class TestTimeout:
    """超时控制测试。"""

    @pytest.mark.asyncio
    async def test_timeout_raises_on_timeout(self) -> None:
        """超时时抛出 LLM_TIMEOUT 错误。"""

        async def slow_task():
            await asyncio.sleep(2.0)

        with pytest.raises(AppException) as exc_info:
            await with_timeout(slow_task(), seconds=0.1)

        assert exc_info.value.code == ErrorCode.LLM_TIMEOUT

    @pytest.mark.asyncio
    async def test_timeout_passes_on_success(self) -> None:
        """正常完成时返回结果。"""

        async def fast_task():
            return "ok"

        result = await with_timeout(fast_task(), seconds=1.0)
        assert result == "ok"


class TestRetry:
    """重试测试。"""

    @pytest.mark.asyncio
    async def test_retry_eventually_succeeds(self) -> None:
        """重试后最终成功。"""
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection failed")
            return "success"

        result = await retry_async(flaky, max_attempts=5, min_wait=0.01, max_wait=0.05)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """重试耗尽后抛出错误。"""

        async def always_fail():
            raise httpx.ConnectError("always fail")

        with pytest.raises(AppException) as exc_info:
            await retry_async(always_fail, max_attempts=2, min_wait=0.01, max_wait=0.02)

        assert exc_info.value.code == ErrorCode.LLM_API_ERROR


class TestCircuitBreaker:
    """熔断器测试。"""

    def setup_method(self) -> None:
        """每个测试前重置熔断器。"""
        reset_circuit_breakers()

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self) -> None:
        """失败达到阈值时打开熔断器。"""
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1)

        async def fail():
            raise ValueError("error")

        # 第一次失败
        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.CLOSED

        # 第二次失败 → 打开熔断器
        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        # 熔断器打开状态下拒绝调用
        with pytest.raises(AppException) as exc_info:
            await cb.call(fail)
        assert exc_info.value.code == ErrorCode.LLM_CIRCUIT_OPEN

    @pytest.mark.asyncio
    async def test_circuit_recovers(self) -> None:
        """熔断后经过 recovery_timeout 进入 HALF_OPEN，成功后恢复 CLOSED。"""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05)

        async def fail():
            raise ValueError("error")

        async def success():
            return "ok"

        # 触发熔断
        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        # 等待恢复窗口
        await asyncio.sleep(0.1)

        # 调用成功 → HALF_OPEN → CLOSED
        result = await cb.call(success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_get_circuit_breaker_singleton(self) -> None:
        """同名熔断器返回同一实例。"""
        cb1 = get_circuit_breaker("test_singleton")
        cb2 = get_circuit_breaker("test_singleton")
        assert cb1 is cb2