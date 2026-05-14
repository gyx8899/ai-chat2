"""DB 模型 - 会话模型。

重构自 app/models/schemas.py - Session 部分。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.database import Base
from app.core.constants import DBConstants, ChatConstants

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# 跨数据库兼容的 UUID 类型
class UUID(TypeDecorator):
    """跨数据库兼容的 UUID 类型。"""

    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = True):
        self.as_uuid = as_uuid
        super().__init__(DBConstants.UUID_LENGTH)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(DBConstants.UUID_LENGTH))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class Session(Base):
    """会话表。"""

    __tablename__ = DBConstants.TABLE_SESSIONS

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(DBConstants.TITLE_MAX_LENGTH),
        default=ChatConstants.DEFAULT_TITLE,
    )
    prompt_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, default=None, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(DBConstants.INDEX_SESSIONS_CREATED_AT, "created_at"),
    )

    def __init__(
        self, title: str = ChatConstants.DEFAULT_TITLE, prompt_type: Optional[str] = None
    ) -> None:
        self.title = title
        self.prompt_type = prompt_type

    def to_dict(self) -> dict:
        """转换为字典。"""
        return {
            "id": str(self.id),
            "title": self.title,
            "prompt_type": self.prompt_type,
            "created_at": int(self.created_at.timestamp() * 1000),
            "updated_at": int(self.updated_at.timestamp() * 1000),
        }


__all__ = ["Session", "UUID"]