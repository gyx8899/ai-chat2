"""Core 模块 - 应用核心层。

提供应用基础设施：异常、常量、配置等。
采用 DDD 分层架构，core 层是基础设施的一部分。
"""

from app.core.exceptions import (
    AppException,
    ErrorCode,
    ERROR_TO_HTTP_STATUS,
    raise_app_error,
)
from app.core.constants import (
    MessageRole,
    APIStatus,
    SSEEvent,
    ProviderConstants,
    ChatConstants,
    DBConstants,
)
from app.core.settings import (
    LLMProvider,
    Settings,
    get_settings,
    settings,
    get_current_config,
)
from app.core.llm_config import LLMConfigManager, get_llm_config_manager

__all__ = [
    # Exceptions
    "AppException",
    "ErrorCode",
    "ERROR_TO_HTTP_STATUS",
    "raise_app_error",
    # Constants
    "MessageRole",
    "APIStatus",
    "SSEEvent",
    "ProviderConstants",
    "ChatConstants",
    "DBConstants",
    # Settings
    "LLMProvider",
    "Settings",
    "get_settings",
    "settings",
    "get_current_config",
    # LLM Config
    "LLMConfigManager",
    "get_llm_config_manager",
]