"""Tests for chat endpoint with prompt integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.prompts.service import PromptService
from app.db.schemas import ChatRequest


class TestChatRequestPromptFields:
    """Test that ChatRequest accepts prompt_id and system_prompt fields."""

    def test_chat_request_with_prompt_id(self) -> None:
        """ChatRequest accepts prompt_id field."""
        req = ChatRequest(query="Hello", prompt_id="frontendAI")
        assert req.prompt_id == "frontendAI"
        assert req.system_prompt is None

    def test_chat_request_with_system_prompt(self) -> None:
        """ChatRequest accepts system_prompt field."""
        req = ChatRequest(query="Hello", system_prompt="Custom system prompt")
        assert req.system_prompt == "Custom system prompt"
        assert req.prompt_id is None

    def test_chat_request_both_fields(self) -> None:
        """ChatRequest accepts both prompt_id and system_prompt."""
        req = ChatRequest(
            query="Hello",
            prompt_id="frontendAI",
            system_prompt="Override prompt",
        )
        assert req.prompt_id == "frontendAI"
        assert req.system_prompt == "Override prompt"

    def test_chat_request_neither_field(self) -> None:
        """ChatRequest works with neither prompt_id nor system_prompt."""
        req = ChatRequest(query="Hello")
        assert req.prompt_id is None
        assert req.system_prompt is None


class TestResolveSystemPromptIntegration:
    """Test resolve_system_prompt behavior in chat context."""

    @pytest.fixture
    def service(self) -> PromptService:
        """Create a service with test config."""
        from app.core.prompts.schemas import PromptConfigFile, PromptTemplate

        svc = PromptService()
        svc._config = PromptConfigFile(
            prompts=[
                PromptTemplate(
                    id="default",
                    type="default",
                    name="Default",
                    description="Default",
                    category="general",
                    content="You are a default assistant.",
                    variables=[],
                    welcome="Hello!",
                    examples=[],
                    preferred_model=None,
                ),
                PromptTemplate(
                    id="frontendAI",
                    type="frontendAI",
                    name="Frontend AI",
                    description="Frontend",
                    category="development",
                    content="You are a frontend expert.",
                    variables=[],
                    welcome="Hi!",
                    examples=[],
                    preferred_model="claude-sonnet-4",
                ),
            ],
            default_type="default",
            metadata={},
        )
        return svc

    def test_override_wins_over_prompt_id(self, service: PromptService) -> None:
        """override takes precedence over prompt_id."""
        text, used_id = service.resolve_system_prompt(
            override="Custom system",
            prompt_id="frontendAI",
            session_id="test",
        )
        assert text == "Custom system"
        assert used_id == "override"

    def test_prompt_id_used_when_valid(self, service: PromptService) -> None:
        """Valid prompt_id is used."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id="frontendAI",
            session_id="test",
        )
        assert "frontend" in text.lower()
        assert used_id == "frontendAI"

    def test_fallback_on_invalid_prompt_id(self, service: PromptService) -> None:
        """Invalid prompt_id falls back to default_type (no exception)."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id="nonexistent",
            session_id="test",
        )
        assert used_id == "default"
        assert "default" in text.lower()

    def test_fallback_when_prompt_id_none(self, service: PromptService) -> None:
        """prompt_id=None falls back to default_type."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id=None,
            session_id="test",
        )
        assert used_id == "default"

    def test_used_prompt_id_different_from_request(self, service: PromptService) -> None:
        """Invalid prompt_id results in different used_id (fallback detected)."""
        _, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id="invalid-type",
            session_id="session-abc",
        )
        assert used_id != "invalid-type"
        assert used_id == "default"