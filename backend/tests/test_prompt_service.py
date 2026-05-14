"""Tests for PromptService."""

import pytest
import pytest_asyncio

from app.core.prompts.schemas import PromptConfigFile, PromptInfo
from app.core.prompts.service import PromptService, get_prompt_service


class TestPromptService:
    """Test suite for PromptService."""

    def _build_config(self) -> PromptConfigFile:
        from app.core.prompts.schemas import PromptTemplate, PromptVariable
        return PromptConfigFile(
            prompts=[
                PromptTemplate(
                    id="default",
                    type="default",
                    name="Default",
                    description="Default prompt",
                    category="general",
                    content="You are a default assistant.\nUser: {user_name}",
                    variables=[PromptVariable(name="user_name", description="User name", default="用户")],
                    welcome="Hello!",
                    examples=[],
                    preferred_model=None,
                ),
                PromptTemplate(
                    id="frontendAI",
                    type="frontendAI",
                    name="Frontend AI",
                    description="Frontend specialist",
                    category="development",
                    content="You are a frontend expert.\nUser: {user_name} | Time: {current_time}",
                    variables=[
                        PromptVariable(name="user_name", description="User name", default="用户"),
                        PromptVariable(name="current_time", description="Time", default=""),
                    ],
                    welcome="Hi Frontend Dev!",
                    examples=[],
                    preferred_model="claude-sonnet-4",
                ),
            ],
            default_type="default",
            metadata={},
        )

    @pytest.fixture
    def service(self) -> PromptService:
        """Create a fresh service instance with test config."""
        svc = PromptService()
        svc._config = self._build_config()
        return svc

    # ─────────────────────────────────────────────────────────────
    # list_info
    # ─────────────────────────────────────────────────────────────

    def test_list_info_returns_all_prompts(self, service: PromptService) -> None:
        """list_info returns PromptInfo for all prompts."""
        infos = service.list_info()
        assert len(infos) == 2
        ids = [i.id for i in infos]
        assert "default" in ids
        assert "frontendAI" in ids

    def test_list_info_excludes_content(self, service: PromptService) -> None:
        """list_info items do NOT contain content or variables."""
        infos = service.list_info()
        for info in infos:
            assert not hasattr(info, "content")
            assert not hasattr(info, "variables")
            assert hasattr(info, "name")
            assert hasattr(info, "welcome")
            assert hasattr(info, "preferred_model")

    def test_list_info_preserves_order(self, service: PromptService) -> None:
        """list_info preserves JSON array order."""
        infos = service.list_info()
        assert infos[0].id == "default"
        assert infos[1].id == "frontendAI"

    # ─────────────────────────────────────────────────────────────
    # get_prompt
    # ─────────────────────────────────────────────────────────────

    def test_get_prompt_existing(self, service: PromptService) -> None:
        """get_prompt returns PromptTemplate for valid id."""
        t = service.get_prompt("default")
        assert t is not None
        assert t.id == "default"
        assert "content" in t.model_dump()

    def test_get_prompt_not_found(self, service: PromptService) -> None:
        """get_prompt returns None for unknown id."""
        t = service.get_prompt("nonexistent")
        assert t is None

    # ─────────────────────────────────────────────────────────────
    # default_type
    # ─────────────────────────────────────────────────────────────

    def test_default_type_returns_config_value(self, service: PromptService) -> None:
        """default_type returns the configured default_type."""
        assert service.default_type() == "default"

    # ─────────────────────────────────────────────────────────────
    # categories
    # ─────────────────────────────────────────────────────────────

    def test_categories_returns_distinct(self, service: PromptService) -> None:
        """categories returns distinct categories from prompts."""
        cats = service.categories()
        assert len(cats) >= 1
        names = [c.value if hasattr(c, "value") else c for c in cats]
        assert "general" in names

    # ─────────────────────────────────────────────────────────────
    # reload
    # ─────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_reload_returns_count(self, service: PromptService) -> None:
        """reload reloads from actual config file and returns count."""
        count = await service.reload()
        # 从 config/prompts.json 加载，实际有 4 个
        assert count == 4

    # ─────────────────────────────────────────────────────────────
    # resolve_system_prompt 优先级
    # ─────────────────────────────────────────────────────────────

    def test_resolve_override_wins(self, service: PromptService) -> None:
        """override parameter has highest priority."""
        text, used_id = service.resolve_system_prompt(
            override="Custom system prompt",
            prompt_id="frontendAI",
            session_id="session-123",
        )
        assert text == "Custom system prompt"
        assert used_id == "override"

    def test_resolve_prompt_id_wins_over_default(
        self, service: PromptService
    ) -> None:
        """prompt_id wins over default_type when both are valid."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id="frontendAI",
            session_id="session-123",
        )
        assert "frontend" in text.lower()
        assert used_id == "frontendAI"

    def test_resolve_falls_back_to_default_type(
        self, service: PromptService
    ) -> None:
        """No override and invalid prompt_id falls back to default_type."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id="nonexistent",
            session_id="session-123",
        )
        assert "default" in text.lower()
        assert used_id == "default"

    def test_resolve_falls_back_when_prompt_id_none(
        self, service: PromptService
    ) -> None:
        """prompt_id=None falls back to default_type."""
        text, used_id = service.resolve_system_prompt(
            override=None,
            prompt_id=None,
            session_id="session-123",
        )
        assert text is not None
        assert used_id == "default"

    def test_resolve_returns_tuple(self, service: PromptService) -> None:
        """resolve_system_prompt returns (text, used_id) tuple."""
        result = service.resolve_system_prompt(
            override=None, prompt_id="default", session_id="s1"
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)


class TestGetPromptService:
    """Test the singleton accessor."""

    def test_get_prompt_service_returns_instance(self) -> None:
        """get_prompt_service returns a PromptService instance."""
        svc = get_prompt_service()
        assert isinstance(svc, PromptService)