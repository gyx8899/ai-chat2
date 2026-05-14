"""DB 模块 - 数据持久化层。

提供数据库配置、ORM 模型和 API Schema。
采用 DDD 分层架构，db 层专注于数据持久化。
"""

from app.db.database import (
    engine,
    AsyncSessionLocal,
    Base,
    get_db,
    init_db,
    close_db,
)
from app.db.models.session import Session, UUID
from app.db.models.message import Message
from app.db.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse,
    MessageResponse,
    MessageListResponse,
    ChatRequest,
    ChatResponse,
    LLMConfig,
)

__all__ = [
    # Database
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    # Models
    "Session",
    "Message",
    "UUID",
    # Schemas
    "SessionCreateRequest",
    "SessionUpdateRequest",
    "SessionResponse",
    "SessionListResponse",
    "MessageResponse",
    "MessageListResponse",
    "ChatRequest",
    "ChatResponse",
    "LLMConfig",
]