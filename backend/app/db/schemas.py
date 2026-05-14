"""DB 模块 - API 请求/响应 Pydantic 模型。

重构自 app/models/api_schemas.py - 采用 DDD 分层架构。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import ChatConstants


class SessionCreateRequest(BaseModel):
    """创建会话请求。"""

    title: str = Field(
        default=ChatConstants.DEFAULT_TITLE,
        max_length=ChatConstants.MAX_TITLE_LENGTH,
        description="会话标题",
    )
    prompt_type: Optional[str] = Field(
        default=None,
        max_length=64,
        description="提示词类型（来自 URL type 参数）",
    )


class SessionUpdateRequest(BaseModel):
    """更新会话请求。"""

    title: str = Field(
        ...,
        min_length=ChatConstants.MIN_TITLE_LENGTH,
        max_length=ChatConstants.MAX_TITLE_LENGTH,
        description="新的会话标题",
    )


class SessionResponse(BaseModel):
    """会话响应。"""

    id: str
    title: str
    prompt_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """会话列表响应。"""

    sessions: list[SessionResponse]


class MessageResponse(BaseModel):
    """消息响应。"""

    id: str
    session_id: str
    role: str
    content: str
    msg_metadata: Optional[dict] = None
    created_at: datetime


class MessageListResponse(BaseModel):
    """消息列表响应。"""

    messages: list[MessageResponse]
    total: int


class ChatRequest(BaseModel):
    """聊天请求。"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=ChatConstants.MAX_MESSAGE_LENGTH,
        description="用户输入",
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="可选的会话 ID",
    )
    model: Optional[str] = Field(
        default=None,
        description="可选的模型 ID，覆盖全局配置",
    )
    prompt_id: Optional[str] = Field(
        default=None,
        description="提示词类型 ID（来自 URL type 参数）",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=ChatConstants.MAX_MESSAGE_LENGTH,
        description="可选的系统提示（最高优先级）",
    )


class ChatResponse(BaseModel):
    """聊天响应。"""

    message: MessageResponse
    session_id: Optional[str] = None


class LLMConfig(BaseModel):
    """LLM 配置。"""

    provider: str = Field(..., description="Provider: mock/openai/ollama")
    model: Optional[str] = Field(default=None, description="模型名称")
    api_base: Optional[str] = Field(default=None, description="API Base URL")
    api_key: Optional[str] = Field(default=None, description="API Key")


__all__ = [
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