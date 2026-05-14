"""Tests for PromptLoader."""

import json
import os
import tempfile
from typing import Any

import pytest

from app.core.prompts.loader import PromptLoader, warn_undeclared_variables
from app.core.prompts.schemas import PromptConfigFile


class TestPromptLoader:
    """Test suite for PromptLoader."""

    def _write_json(self, path: str, data: dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _make_valid_config(self, **overrides: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "prompts": [
                {
                    "id": "default",
                    "type": "default",
                    "name": "Default",
                    "description": "Default prompt",
                    "category": "general",
                    "content": "You are a helpful assistant.\n\nUser: {user_name}",
                    "variables": [{"name": "user_name", "description": "User name", "default": "User"}],
                    "welcome": "Hello!",
                    "examples": [],
                    "preferred_model": None,
                }
            ],
            "default_type": "default",
            "metadata": {},
        }
        base.update(overrides)
        return base

    # ─────────────────────────────────────────────────────────────
    # 场景 1: 合法配置
    # ─────────────────────────────────────────────────────────────

    def test_load_valid_config(self) -> None:
        """Load a valid prompts.json successfully."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(self._make_valid_config(), f)
            path = f.name
        try:
            loader = PromptLoader(path)
            config = loader.load()
            assert isinstance(config, PromptConfigFile)
            assert len(config.prompts) == 1
            assert config.default_type == "default"
        finally:
            os.unlink(path)

    # ─────────────────────────────────────────────────────────────
    # 场景 2: 结构错误（缺少必填字段）
    # ─────────────────────────────────────────────────────────────

    def test_load_missing_required_field_raises(self) -> None:
        """Missing required 'prompts' field raises RuntimeError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"default_type": "default"}, f)
            path = f.name
        try:
            loader = PromptLoader(path)
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()
            assert "ValidationError" in str(exc_info.value) or "prompts" in str(
                exc_info.value
            )
        finally:
            os.unlink(path)

    def test_load_prompt_missing_id_raises(self) -> None:
        """Prompt missing 'id' field raises RuntimeError."""
        data = self._make_valid_config()
        data["prompts"][0].pop("id")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = PromptLoader(path)
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()
            assert "id" in str(exc_info.value).lower() or "ValidationError" in str(
                exc_info.value
            )
        finally:
            os.unlink(path)

    # ─────────────────────────────────────────────────────────────
    # 场景 3: 业务错误（default_type 不存在）
    # ─────────────────────────────────────────────────────────────

    def test_load_default_type_not_exist_raises(self) -> None:
        """default_type pointing to non-existent id raises RuntimeError."""
        data = self._make_valid_config(default_type="nonexistent")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = PromptLoader(path)
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()
            assert "default_type" in str(exc_info.value) or "not found" in str(
                exc_info.value
            )
        finally:
            os.unlink(path)

    def test_load_duplicate_id_raises(self) -> None:
        """Duplicate prompt ids raise RuntimeError (business check)."""
        data = self._make_valid_config()
        data["prompts"].append(data["prompts"][0].copy())
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = PromptLoader(path)
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()
            assert "duplicate" in str(exc_info.value).lower() or "id" in str(
                exc_info.value
            )
        finally:
            os.unlink(path)

    # ─────────────────────────────────────────────────────────────
    # 场景 4: 未声明变量 WARN
    # ─────────────────────────────────────────────────────────────

    def test_warn_undeclared_variables_no_exception(self) -> None:
        """Content with undeclared {var} does NOT raise (just warns)."""
        data = self._make_valid_config()
        data["prompts"][0][
            "content"
        ] = "User: {user_name} | Extra: {undeclared} | {another_one}"
        data["prompts"][0]["variables"] = [
            {"name": "user_name", "description": "User name", "default": "User"}
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            loader = PromptLoader(path)
            config = loader.load()
            # 函数执行无异常（仅记录 warning）
            warn_undeclared_variables(config)
        finally:
            os.unlink(path)

    def test_warn_no_extra_vars_no_exception(self) -> None:
        """All declared variables produce no warning (no exception)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(self._make_valid_config(), f)
            path = f.name
        try:
            loader = PromptLoader(path)
            config = loader.load()
            # 执行不抛异常
            warn_undeclared_variables(config)
        finally:
            os.unlink(path)

    # ─────────────────────────────────────────────────────────────
    # 场景 5: 文件缺失（降级到内置默认）
    # ─────────────────────────────────────────────────────────────

    def test_load_file_not_found_fallback(self) -> None:
        """Missing file falls back to built-in default."""
        loader = PromptLoader("/nonexistent/path/prompts.json")
        config = loader.load()
        assert isinstance(config, PromptConfigFile)
        assert len(config.prompts) >= 1
        assert any(p.id == "default" for p in config.prompts)