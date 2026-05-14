"""DB 模型 - 消息模型。

重构自 app/models/schemas.py - Message 部分。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text, Index, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.session import UUID
from app.core.constants import DBConstants

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class Message(Base):
    """消息表。"""

    __tablename__ = DBConstants.TABLE_MESSAGES

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    role: Mapped[str] = mapped_column(String(DBConstants.ROLE_MAX_LENGTH))
    content: Mapped[str] = mapped_column(Text)
    msg_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index(DBConstants.INDEX_MESSAGES_SESSION_CREATED, "session_id", "created_at"),
    )

    def __init__(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        msg_metadata: Optional[dict] = None,
    ) -> None:
        self.session_id = session_id
        self.role = role
        self.content = content
        self.msg_metadata = msg_metadata

    def to_dict(self) -> dict:
        """转换为字典。"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "role": self.role,
            "content": self.content,
            "msg_metadata": self.msg_metadata,
            "created_at": int(self.created_at.timestamp() * 1000),
        }


__all__ = ["Message"]