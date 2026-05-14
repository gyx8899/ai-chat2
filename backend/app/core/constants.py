"""Core 模块 - 应用常量。

集中管理所有魔法数字/字符串/枚举。
"""

from enum import Enum


# ============================================================================
# 消息角色
# ============================================================================


class MessageRole(str, Enum):
    """聊天消息角色枚举。"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


# ============================================================================
# API 状态码与 SSE 事件类型
# ============================================================================


class APIStatus:
    """HTTP 状态码常量。"""

    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


class SSEEvent:
    """SSE 事件类型常量。"""

    MESSAGE = "message"
    ERROR = "error"
    DONE = "done"


# ============================================================================
# Provider 常量（统一管理）
# ============================================================================


class ProviderConstants:
    """Provider 名称和默认配置常量。"""

    # Provider 名称（唯一真实来源）
    MOCK = "mock"
    OPENAI = "openai"
    OLLAMA = "ollama"

    # OpenAI 模型前缀（用于自动推断 Provider）
    OPENAI_MODEL_PREFIXES = ("gpt-", "text-", "embedding-", "o1-", "chatgpt-")

    # Ollama 模型前缀（用于自动推断 Provider）
    OLLAMA_MODEL_PREFIXES = ("llama", "qwen", "deepseek", "gemma", "mistral", "phi")

    # 默认超时（秒）
    DEFAULT_TIMEOUT = 60.0
    OPENAI_TIMEOUT = 60.0
    OLLAMA_TIMEOUT = 120.0


# ============================================================================
# 聊天相关常量
# ============================================================================


class ChatConstants:
    """聊天功能常量。"""

    # 查询限制
    DEFAULT_SESSION_LIMIT = 50
    DEFAULT_MESSAGE_LIMIT = 100

    # 标题长度
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 100
    DEFAULT_TITLE = "新对话"

    # 消息长度
    MAX_MESSAGE_LENGTH = 10000

    # 最大上下文消息数
    MAX_CONTEXT_MESSAGES = 20


# ============================================================================
# 数据库相关常量
# ============================================================================


class DBConstants:
    """数据库相关常量。"""

    # 表名
    TABLE_SESSIONS = "sessions"
    TABLE_MESSAGES = "messages"

    # 索引名
    INDEX_MESSAGES_SESSION_CREATED = "idx_messages_session_created"
    INDEX_SESSIONS_CREATED_AT = "idx_sessions_created_at"

    # 字段长度
    UUID_LENGTH = 36
    TITLE_MAX_LENGTH = 100
    ROLE_MAX_LENGTH = 20
    CONTENT_MAX_LENGTH = 65535  # TEXT 类型


# 向后兼容别名
__all__ = [
    "MessageRole",
    "APIStatus",
    "SSEEvent",
    "ProviderConstants",
    "ChatConstants",
    "DBConstants",
]