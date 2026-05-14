"""会话管理路由。

重构后使用新模块路径。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.constants import APIStatus, ChatConstants
from app.db.schemas import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionUpdateRequest,
    MessageListResponse,
    MessageResponse,
)
from app.domain.session import MemoryService

router = APIRouter()


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    prompt_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """获取会话列表（按创建时间倒序）。

    - prompt_type 为 None 时返回全部
    - prompt_type == default 时包含 NULL 旧会话
    - 其他 prompt_type 严格等值
    """
    sessions = await MemoryService.get_sessions(db, prompt_type=prompt_type)
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s["id"],
                title=s["title"],
                prompt_type=s.get("prompt_type"),
                created_at=s["created_at"],
                updated_at=s["updated_at"],
            )
            for s in sessions
        ]
    )


@router.post(
    "/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """创建新会话。"""
    session = await MemoryService.create_session(
        db, title=request.title, prompt_type=request.prompt_type
    )
    return SessionResponse(
        id=session["id"],
        title=session["title"],
        prompt_type=session.get("prompt_type"),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """获取单个会话详情。"""
    session = await MemoryService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=APIStatus.NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    return SessionResponse(
        id=session["id"],
        title=session["title"],
        prompt_type=session.get("prompt_type"),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """更新会话标题。"""
    updated = await MemoryService.update_session(db, session_id, request.title)
    if not updated:
        raise HTTPException(
            status_code=APIStatus.NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    session = await MemoryService.get_session(db, session_id)
    assert session is not None
    return SessionResponse(
        id=session["id"],
        title=session["title"],
        prompt_type=session.get("prompt_type"),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除会话（级联删除消息）。"""
    deleted = await MemoryService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=APIStatus.NOT_FOUND,
            detail=f"Session {session_id} not found",
        )


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
    limit: int = ChatConstants.DEFAULT_MESSAGE_LIMIT,
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """获取会话的消息列表。"""
    session = await MemoryService.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=APIStatus.NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    messages = await MemoryService.get_messages(db, session_id, limit=limit)
    return MessageListResponse(
        messages=[
            MessageResponse(
                id=m["id"],
                session_id=m["session_id"],
                role=m["role"],
                content=m["content"],
                msg_metadata=m.get("msg_metadata"),
                created_at=m["created_at"],
            )
            for m in messages
        ],
        total=len(messages),
    )