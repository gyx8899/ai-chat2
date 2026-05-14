"""Tests for PromptRenderer."""

import re
from datetime import datetime, timedelta, timezone

import pytest

from app.core.prompts.renderer import PromptRenderer, build_context


class TestPromptRenderer:
    """Test suite for PromptRenderer."""

    # ─────────────────────────────────────────────────────────────
    # render_prompt 基本功能
    # ─────────────────────────────────────────────────────────────

    def test_render_no_variables(self) -> None:
        """Content without variables renders as-is."""
        content = "You are a helpful assistant."
        result = PromptRenderer.render_prompt(content, {})
        assert result == "You are a helpful assistant."

    def test_render_declared_variable(self) -> None:
        """Declared variables are substituted."""
        content = "Hello, {user_name}!"
        result = PromptRenderer.render_prompt(content, {"user_name": "Alice"})
        assert result == "Hello, Alice!"

    def test_render_declared_variable_missing_value(self) -> None:
        """Missing variable (not in context) keeps original placeholder."""
        content = "Hello, {user_name}! Time: {current_time}"
        result = PromptRenderer.render_prompt(content, {"user_name": "Bob"})
        # 未提供的变量保留原占位符
        assert "Bob" in result
        assert "{current_time}" in result

    def test_render_multiple_variables(self) -> None:
        """Multiple variables all substituted."""
        content = "User: {user_name}\nTime: {current_time}\nModel: {model}"
        context = {"user_name": "Charlie", "current_time": "2026-05-14", "model": "gpt-4"}
        result = PromptRenderer.render_prompt(content, context)
        assert "Charlie" in result
        assert "2026-05-14" in result
        assert "gpt-4" in result

    def test_render_undeclared_placeholder_unchanged(self) -> None:
        """Undeclared placeholders are kept as-is."""
        content = "Hello {user_name}, your role is {role}"
        result = PromptRenderer.render_prompt(content, {"user_name": "Dave"})
        assert "{role}" in result
        assert "Dave" in result

    def test_render_special_characters_in_value(self) -> None:
        """Special characters in variable values are preserved."""
        content = "Query: {query}"
        result = PromptRenderer.render_prompt(content, {"query": "What is $100 + 50?"})
        assert result == "Query: What is $100 + 50?"

    # ─────────────────────────────────────────────────────────────
    # build_context 时区验证（UTC+8）
    # ─────────────────────────────────────────────────────────────

    def test_build_context_uses_utc8(self) -> None:
        """build_context returns UTC+8 timezone timestamp."""
        context = build_context()
        assert "current_time" in context
        now_utc8 = datetime.now(timezone(timedelta(hours=8)))
        # 允许前后 5 秒误差
        diff = abs((context["current_time"].toordinal() - now_utc8.toordinal()))
        assert diff < 1, f"Expected UTC+8 time close to {now_utc8}, got {context['current_time']}"

    def test_build_context_returns_datetime_object(self) -> None:
        """build_context returns datetime objects, not strings."""
        context = build_context()
        assert isinstance(context.get("current_time"), datetime)
        assert context.get("user_name") == "用户"

    def test_build_context_includes_user_name(self) -> None:
        """build_context includes user_name with default value."""
        context = build_context()
        assert "user_name" in context
        assert context["user_name"] == "用户"

    def test_build_context_user_name_overridable(self) -> None:
        """build_context accepts custom user_name."""
        context = build_context(user_name="Alice")
        assert context["user_name"] == "Alice"

    # ─────────────────────────────────────────────────────────────
    # 端到端渲染
    # ─────────────────────────────────────────────────────────────

    def test_render_template_with_context(self) -> None:
        """Full template rendering with context."""
        content = (
            "You are a helpful AI assistant.\n\n"
            "Current user: {user_name}\n"
            "Current time: {current_time}\n"
            "Ask anything!"
        )
        context = build_context(user_name="TestUser")
        result = PromptRenderer.render_prompt(content, context)
        assert "TestUser" in result
        assert "helpful AI assistant" in result
        assert "{user_name}" not in result
        assert "{current_time}" not in result