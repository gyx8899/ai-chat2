"""Domain Session 模块 - 会话记忆服务。

重构自 app/services/memory_service.py - 采用 DDD 分层架构。
"""

import uuid
from typing import Optional, Union

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session import Session as ChatSession
from app.db.models.message import Message as ChatMessage
from app.core.constants import ChatConstants, MessageRole


class MemoryService:
    """会话与消息记忆服务。"""

    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        prompt_type: Optional[str] = None,
    ) -> list[dict]:
        """获取会话列表（按创建时间倒序）。

        NULL 兼容过滤：
        - prompt_type == default_type 时：包含 prompt_type == default_type 和 NULL（旧会话）
        - prompt_type 为其他值时：严格等值
        - prompt_type 为 None 时：不过滤，返回全部
        """
        from app.core.prompts.service import get_prompt_service

        default_type = get_prompt_service().default_type()
        ptype: Optional[str] = prompt_type

        stmt = select(ChatSession)

        if ptype is not None:
            if ptype == default_type:
                # 默认 type 标签：包含 NULL（旧会话）
                stmt = stmt.where(
                    (ChatSession.prompt_type == ptype)
                    | (ChatSession.prompt_type.is_(None))
                )
            else:
                # 其他 type：严格等值
                stmt = stmt.where(ChatSession.prompt_type == ptype)

        stmt = stmt.order_by(desc(ChatSession.created_at))
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        return [s.to_dict() for s in sessions]

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[dict]:
        """获取单个会话。"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        return session.to_dict() if session else None

    @staticmethod
    async def create_session(
        db: AsyncSession,
        title: str = ChatConstants.DEFAULT_TITLE,
        prompt_type: Optional[str] = None,
    ) -> dict:
        """创建新会话。"""
        session = ChatSession(title=title, prompt_type=prompt_type)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session.to_dict()

    @staticmethod
    async def update_session(
        db: AsyncSession, session_id: str, title: str
    ) -> bool:
        """更新会话标题。"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return False
        session.title = title
        await db.commit()
        return True

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> bool:
        """删除会话（级联删除消息）。"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return False
        # 级联删除消息
        await db.execute(
            delete(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        # 删除会话
        await db.delete(session)
        await db.commit()
        return True

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        session_id: str,
        limit: int = ChatConstants.DEFAULT_MESSAGE_LIMIT,
    ) -> list[dict]:
        """获取会话的消息列表。"""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        messages = result.scalars().all()
        return [m.to_dict() for m in messages]

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """添加消息。"""
        message = ChatMessage(
            session_id=uuid.UUID(session_id),
            role=role,
            content=content,
            msg_metadata=metadata,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # 如果是第一条用户消息，自动更新会话标题
        if role == MessageRole.USER.value:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session_obj = result.scalar_one_or_none()
            if (
                session_obj is not None
                and session_obj.title == ChatConstants.DEFAULT_TITLE
            ):
                session_obj.title = content[:ChatConstants.MAX_TITLE_LENGTH]
                await db.commit()

        return message.to_dict()


__all__ = ["MemoryService"]