"""聊天路由 - 对齐原项目 SSE 协议 + 消息持久化 + 心跳保活。

重构后使用新模块路径。
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import APIStatus, ChatConstants, MessageRole, SSEEvent
from app.core.prompts.service import get_prompt_service
from app.db.database import AsyncSessionLocal
from app.db.schemas import ChatRequest, ChatResponse, MessageResponse
from app.domain.llm import (
    chat_stream,
    format_content_frame,
    format_done_frame,
    format_error_frame,
    format_heartbeat_frame,
    format_meta_frame,
)
from app.domain.session import MemoryService
from app.knowledge import retrieve_context

logger = logging.getLogger(__name__)

router = APIRouter()

# 验证正则
_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

# 心跳间隔（秒）- 对齐设计文档 §2.2.4
HEARTBEAT_INTERVAL = 15.0


def _validate_chat_request(request: ChatRequest) -> str:
    """校验聊天请求，返回清理后的 query。"""
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=APIStatus.BAD_REQUEST,
            detail="Query cannot be empty",
        )

    query = request.query.strip()
    if len(query) > ChatConstants.MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=APIStatus.BAD_REQUEST,
            detail=f"Query too long (max {ChatConstants.MAX_MESSAGE_LENGTH} chars)",
        )

    # 验证 session_id 格式（如果提供）
    if request.session_id and not _SESSION_ID_PATTERN.match(request.session_id):
        raise HTTPException(
            status_code=APIStatus.BAD_REQUEST,
            detail="Invalid session_id format",
        )

    return query


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """处理对话请求（同步等待完整回复）。"""
    query = _validate_chat_request(request)

    # 解析 system prompt
    service = get_prompt_service()
    system_text, _ = service.resolve_system_prompt(
        override=request.system_prompt,
        prompt_id=request.prompt_id,
        session_id=request.session_id or "new",
    )

    messages = [
        {"role": MessageRole.SYSTEM.value, "content": system_text},
        {"role": MessageRole.USER.value, "content": query},
    ]

    # 调用 LLM（收集完整响应）
    full_response = ""
    async for token in chat_stream(messages, session_id=request.session_id, model=request.model):
        full_response += token

    return ChatResponse(
        message=MessageResponse(
            id="",
            session_id=request.session_id or "",
            role=MessageRole.ASSISTANT.value,
            content=full_response,
            created_at=datetime.now(),
        ),
        session_id=request.session_id,
    )


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    http_request: Request,
) -> StreamingResponse:
    """流式对话（SSE，对齐原项目协议）。

    协议：
    - meta 帧（RAG hint）→ content 帧（token 流）→ [DONE]
    - 异常时发送 error 帧 + [DONE]
    - 心跳每 15s 一次（: heartbeat）
    """
    query = _validate_chat_request(request)

    return StreamingResponse(
        _sse_generator(query, request, http_request),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _sse_generator(
    query: str,
    request: ChatRequest,
    http_request: Request,
) -> AsyncGenerator[str, None]:
    """SSE 事件生成器 - 对齐原项目协议。

    流程：
    1. RAG 检索 → 发送 meta 帧
    2. 保存用户消息
    3. 流式调用 LLM → 发送 content 帧
    4. 保存 assistant 消息
    5. 发送 [DONE]

    异常处理：
    - 客户端断开 → 退出循环（释放资源），已生成部分持久化
    - LLM 异常 → 发送 error 帧 + [DONE]，已生成部分持久化并标记 [已中断]
    """
    session_id = request.session_id
    full_content = ""
    client_closed = False

    async def _save_message(
        sid: str, role: str, content: str, metadata: Optional[dict] = None
    ) -> None:
        """保存单条消息到数据库（独立 session，保证 commit）。"""
        db = AsyncSessionLocal()
        try:
            session = await MemoryService.get_session(db, sid)
            if session:
                await MemoryService.add_message(db, sid, role, content, metadata)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.warning(f"Failed to save message ({role}): {e}")
        finally:
            await db.close()

    try:
        # 1. RAG 检索
        rag_result = retrieve_context(query)

        # 2. 保存用户消息
        if session_id:
            await _save_message(session_id, MessageRole.USER.value, query)

        # 3. 加载历史上下文（仅读取，无需 commit）
        history = []
        if session_id:
            try:
                db = AsyncSessionLocal()
                try:
                    history_msgs = await MemoryService.get_messages(
                        db, session_id, limit=ChatConstants.MAX_CONTEXT_MESSAGES
                    )
                    # 排除刚保存的用户消息
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in history_msgs[:-1]
                    ]
                finally:
                    await db.close()
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")

        # 用户内容（含 RAG 上下文）
        user_content = query
        if rag_result:
            user_content += f"\n\n[参考资料]\n{rag_result.context}"

        # 4. 解析 system prompt（优先级：override > prompt_id > default_type）
        service = get_prompt_service()
        system_text, used_prompt_id = service.resolve_system_prompt(
            override=request.system_prompt,
            prompt_id=request.prompt_id,
            session_id=session_id or "new",
        )

        # 确定最终使用的模型
        resolved_model = request.model

        messages = (
            [{"role": MessageRole.SYSTEM.value, "content": system_text}]
            + history
            + [{"role": MessageRole.USER.value, "content": user_content}]
        )

        # 5. 发送 RAG meta 首帧
        if rag_result:
            yield format_meta_frame({"ragHint": rag_result.hint})

        # 6. 流式调用 LLM
        last_heartbeat = asyncio.get_event_loop().time()

        async for token in chat_stream(messages, session_id=session_id, model=resolved_model):
            # 检测客户端是否断开
            if await http_request.is_disconnected():
                client_closed = True
                logger.info(f"Client disconnected for session {session_id}")
                break

            full_content += token
            yield format_content_frame(token)

            # 心跳检查
            now = asyncio.get_event_loop().time()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                yield format_heartbeat_frame()
                last_heartbeat = now

        # 7. 正常结束
        if not client_closed:
            yield format_done_frame()

    except Exception as e:
        logger.error(f"Chat stream error: {e}", exc_info=True)
        if not client_closed:
            yield format_error_frame(str(e))
            yield format_done_frame()

    finally:
        # 8. 持久化 assistant 消息（断开时标记 [已中断]）
        if session_id and full_content:
            final_content = (
                f"{full_content}\n\n[已中断]" if client_closed else full_content
            )
            await _save_message(
                session_id,
                MessageRole.ASSISTANT.value,
                final_content,
                {"prompt_id": used_prompt_id, "model_id": resolved_model},
            )