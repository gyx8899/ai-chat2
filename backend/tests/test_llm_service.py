"""Tests for LLM service."""

import pytest

from app.core.settings import LLMProvider, get_settings
from app.core.constants import ProviderConstants
from app.domain.llm import (
    chat_stream,
    format_content_frame,
    format_done_frame,
    format_error_frame,
    format_heartbeat_frame,
    format_meta_frame,
    get_current_llm_config,
)


@pytest.mark.asyncio
class TestLLMService:
    """Test suite for LLM service."""

    async def test_mock_stream(self) -> None:
        """Test mock provider streaming response - now returns plain tokens."""
        # 确保使用 mock provider
        settings = get_settings()
        settings.llm.provider = LLMProvider.MOCK

        messages = [{"role": "user", "content": "hello"}]

        tokens = []
        async for token in chat_stream(messages):
            tokens.append(token)

        # 验证 token 流为纯文本，无 SSE 格式
        assert len(tokens) > 0
        combined = "".join(tokens)
        # 确保是纯文本，不含 SSE 格式
        assert "data:" not in combined
        assert "event:" not in combined

    async def test_mock_response_keywords(self) -> None:
        """Test mock provider keyword-based responses."""
        # 确保使用 mock provider
        settings = get_settings()
        settings.llm.provider = LLMProvider.MOCK

        # 测试 "hello" 关键词
        messages = [{"role": "user", "content": "hello"}]

        tokens = []
        async for token in chat_stream(messages):
            tokens.append(token)

        result = "".join(tokens)
        assert "你好" in result or "帮助" in result

    def test_get_current_config(self) -> None:
        """Test getting current LLM config."""
        config = get_current_llm_config()
        assert "provider" in config
        assert "model" in config
        assert config["provider"] in [
            ProviderConstants.MOCK,
            ProviderConstants.OPENAI,
            ProviderConstants.OLLAMA,
        ]

    def test_provider_constants(self) -> None:
        """Test ProviderConstants values."""
        assert ProviderConstants.MOCK == "mock"
        assert ProviderConstants.OPENAI == "openai"
        assert ProviderConstants.OLLAMA == "ollama"
        assert ProviderConstants.DEFAULT_TIMEOUT > 0


class TestSSEFrames:
    """Test SSE 帧格式工具函数 - 对齐原项目议。"""

    def test_format_content_frame(self) -> None:
        """内容帧格式: data: {\"content\":\"x\"}\\n\\n"""
        frame = format_content_frame("hello")
        assert frame == 'data: {"content": "hello"}\n\n'

    def test_format_content_frame_chinese(self) -> None:
        """支持中文字符（ensure_ascii=False）。"""
        frame = format_content_frame("你好")
        assert "你好" in frame
        assert frame.startswith("data: ")
        assert frame.endswith("\n\n")

    def test_format_error_frame(self) -> None:
        """错误帧格式: data: {\"error\":\"x\"}\\n\\n"""
        frame = format_error_frame("test error")
        assert frame == 'data: {"error": "test error"}\n\n'

    def test_format_meta_frame(self) -> None:
        """元数据帧: data: {\"meta\":{...}}\\n\\n"""
        frame = format_meta_frame({"ragHint": "react-hooks"})
        assert "meta" in frame
        assert "ragHint" in frame
        assert frame.endswith("\n\n")

    def test_format_done_frame(self) -> None:
        """结束帧: data: [DONE]\\n\\n"""
        frame = format_done_frame()
        assert frame == "data: [DONE]\n\n"

    def test_format_heartbeat_frame(self) -> None:
        """心跳帧（注释行）。"""
        frame = format_heartbeat_frame()
        assert frame == ": heartbeat\n\n"