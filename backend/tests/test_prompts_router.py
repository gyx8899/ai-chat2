"""Tests for prompts router."""

import pytest
from starlette.testclient import TestClient

from app.core.prompts.service import get_prompt_service
from app.main import app

client = TestClient(app)


class TestPromptsRouter:
    """Test suite for prompts router endpoints."""

    @pytest.fixture(autouse=True, scope="class")
    def setup(cls) -> None:
        """Ensure prompts service is initialized before each test.

        TestClient does NOT trigger lifespan events, so we init manually.
        """
        import asyncio
        svc = get_prompt_service()
        asyncio.get_event_loop().run_until_complete(svc.init())

    # ─────────────────────────────────────────────────────────────
    # GET /api/v1/config/prompts/  → list
    # ─────────────────────────────────────────────────────────────

    def test_list_prompts_returns_200(self) -> None:
        """List endpoint returns 200."""
        response = client.get("/api/v1/config/prompts/")
        assert response.status_code == 200

    def test_list_prompts_has_required_fields(self) -> None:
        """List response contains prompts, default_type, categories."""
        response = client.get("/api/v1/config/prompts/")
        data = response.json()
        assert "prompts" in data
        assert "default_type" in data
        assert "categories" in data

    def test_list_prompts_no_content(self) -> None:
        """List prompts do NOT contain 'content' or 'variables'."""
        response = client.get("/api/v1/config/prompts/")
        data = response.json()
        for prompt in data["prompts"]:
            assert "content" not in prompt, "Prompt list must NOT contain 'content'"
            assert "variables" not in prompt, "Prompt list must NOT contain 'variables'"

    def test_list_prompts_has_public_fields(self) -> None:
        """List prompts contain expected public fields."""
        response = client.get("/api/v1/config/prompts/")
        data = response.json()
        assert len(data["prompts"]) > 0
        for prompt in data["prompts"]:
            assert "id" in prompt
            assert "name" in prompt
            assert "description" in prompt
            assert "category" in prompt
            assert "welcome" in prompt
            assert "examples" in prompt
            assert "preferred_model" in prompt

    def test_list_preserves_order(self) -> None:
        """List preserves JSON array order."""
        response = client.get("/api/v1/config/prompts/")
        ids = [p["id"] for p in response.json()["prompts"]]
        assert ids[0] == "default"

    # ─────────────────────────────────────────────────────────────
    # GET /api/v1/config/prompts/{type_id}  → detail
    # ─────────────────────────────────────────────────────────────

    def test_get_prompt_existing_returns_200(self) -> None:
        """Get existing prompt returns 200 with content."""
        response = client.get("/api/v1/config/prompts/default")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "default"
        assert "content" in data

    def test_get_prompt_not_found_returns_404(self) -> None:
        """Get nonexistent prompt returns 404."""
        response = client.get("/api/v1/config/prompts/nonexistent-prompt-id")
        assert response.status_code == 404

    # ─────────────────────────────────────────────────────────────
    # POST /api/v1/config/prompts/reload  → auth
    # ─────────────────────────────────────────────────────────────

    def test_reload_no_secret_returns_401(self) -> None:
        """Reload without secret returns 401."""
        response = client.post("/api/v1/config/prompts/reload")
        assert response.status_code == 401

    def test_reload_wrong_secret_returns_401(self) -> None:
        """Reload with wrong secret returns 401."""
        response = client.post("/api/v1/config/prompts/reload?secret=wrong-secret")
        assert response.status_code == 401

    def test_reload_correct_secret_returns_200(self) -> None:
        """Reload with correct secret returns 200 and count."""
        response = client.post(
            "/api/v1/config/prompts/reload",
            params={"secret": "reload-secret-change-me"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["count"] >= 1