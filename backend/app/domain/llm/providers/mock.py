"""Domain LLM Providers 模块 - Mock Provider 实现。"""

import asyncio
from typing import AsyncGenerator, Optional

from app.core.settings import get_settings
from app.domain.llm.providers.base import (
    LLMProviderProtocol,
    LLMResponse,
)


class MockProvider(LLMProviderProtocol):
    """Mock Provider（开发测试用）。"""

    # 预设回复规则
    MOCK_RESPONSES: dict[str, str] = {
        "hello": "你好！有什么可以帮助你的吗？",
        "hi": "你好！很高兴见到你！",
        "who are you": "我是一个 AI 编程助手，由 FastAPI 后端驱动。我可以回答问题、帮助编程、聊天对话等。",
        "help": "我可以帮你：\n1. 回答问题\n2. 编写代码\n3. 解释概念\n4. 写作和翻译\n\n有什么我可以帮你的吗？",
    }

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "mock"

    def get_api_config(self) -> dict:
        return {
            "stream_delay": self._settings.llm.stream_delay,
        }

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """Mock 流式输出（打字机效果）。"""
        config = self.get_api_config()
        delay = config["stream_delay"]

        last_msg = messages[-1]["content"].lower().strip() if messages else ""
        response_text = self.MOCK_RESPONSES.get(
            last_msg,
            "【Mock 模式】当前使用的是模拟模型，返回的是固定回复，不会真正调用 LLM。请在设置中切换到真实模型（如 OpenAI、Ollama）以获得实际的 AI 响应。",
        )

        for char in response_text:
            yield LLMResponse(content=char)
            await asyncio.sleep(delay)

        yield LLMResponse(done=True)


__all__ = ["MockProvider"]