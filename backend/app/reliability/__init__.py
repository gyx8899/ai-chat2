"""Reliability 模块 - 可靠性治理。

重构自 app/reliability.py - 超时、重试、熔断器。
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import AppException, ErrorCode

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# 超时控制
# ============================================================================


async def with_timeout(
    coro: Awaitable[T],
    seconds: float,
    error_message: str = "Operation timed out",
) -> T:
    """为协程添加超时控制。

    Args:
        coro: 协程对象
        seconds: 超时时间（秒）
        error_message: 超时错误消息

    Raises:
        AppException(LLM_TIMEOUT): 超时时
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise AppException(
            ErrorCode.LLM_TIMEOUT,
            f"{error_message} (timeout={seconds}s)",
        )


# ============================================================================
# 重试（指数退避）
# ============================================================================

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
    ConnectionError,
    asyncio.TimeoutError,
)


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    **kwargs: Any,
) -> T:
    """异步重试（指数退避）。

    Args:
        func: 异步函数
        max_attempts: 最大尝试次数（含首次）
        min_wait: 最小等待（秒）
        max_wait: 最大等待（秒）

    Raises:
        AppException(LLM_API_ERROR): 所有重试失败
    """
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            reraise=True,
        ):
            with attempt:
                result = await func(*args, **kwargs)
                return result
    except RetryError as e:
        raise AppException(
            ErrorCode.LLM_API_ERROR,
            f"Retry exhausted after {max_attempts} attempts: {e.last_attempt.exception()}",
        )
    except RETRYABLE_EXCEPTIONS as e:
        raise AppException(
            ErrorCode.LLM_API_ERROR,
            f"Retryable error: {e}",
        )

    raise RuntimeError("unreachable")


# ============================================================================
# 熔断器（Circuit Breaker）
# ============================================================================


class CircuitState(str, Enum):
    """熔断器状态。"""

    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断中
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


@dataclass
class CircuitBreaker:
    """熔断器 - 基于滑动窗口的错误计数。

    状态转换：
    - CLOSED → OPEN: 窗口内错误数 >= failure_threshold
    - OPEN → HALF_OPEN: 经过 recovery_timeout 秒
    - HALF_OPEN → CLOSED: 成功一次
    - HALF_OPEN → OPEN: 失败一次
    """

    name: str
    failure_threshold: int = 5  # 连续失败次数
    recovery_timeout: float = 30.0  # 恢复等待时间（秒）
    state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _last_failure_time: float = 0.0

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """通过熔断器调用函数。

        Raises:
            AppException(LLM_CIRCUIT_OPEN): 熔断器打开时
        """
        # OPEN 状态：检查是否应该进入 HALF_OPEN
        if self.state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                logger.info(f"[circuit:{self.name}] transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise AppException(
                    ErrorCode.LLM_CIRCUIT_OPEN,
                    f"Circuit breaker '{self.name}' is OPEN (will retry in "
                    f"{self.recovery_timeout - (time.time() - self._last_failure_time):.1f}s)",
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """成功调用处理。"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"[circuit:{self.name}] recovered, transitioning to CLOSED")
            self.state = CircuitState.CLOSED
        self._failure_count = 0

    def _on_failure(self) -> None:
        """失败调用处理。"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"[circuit:{self.name}] HALF_OPEN failed, back to OPEN")
            self.state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            logger.warning(
                f"[circuit:{self.name}] threshold reached ({self._failure_count}), OPEN"
            )
            self.state = CircuitState.OPEN


# 全局熔断器实例（按 Provider 维度）
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
) -> CircuitBreaker:
    """获取或创建熔断器（单例）。"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _circuit_breakers[name]


def reset_circuit_breakers() -> None:
    """仅供测试：重置所有熔断器。"""
    _circuit_breakers.clear()


__all__ = [
    "with_timeout",
    "retry_async",
    "CircuitState",
    "CircuitBreaker",
    "get_circuit_breaker",
    "reset_circuit_breakers",
]