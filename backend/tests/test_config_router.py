"""Tests for config router."""

import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """Create an async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
class TestConfigRouter:
    """Test suite for config REST API."""

    async def test_get_config(self, client: AsyncClient) -> None:
        """Test getting current config."""
        response = await client.get("/api/v1/config/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "provider" in data
        assert "model" in data
        assert "available_providers" in data
        assert "mock" in data["available_providers"]
        assert "openai" in data["available_providers"]
        assert "ollama" in data["available_providers"]

    async def test_update_config_mock(self, client: AsyncClient) -> None:
        """Test updating config to mock provider."""
        response = await client.post(
            "/api/v1/config/",
            json={"provider": "mock", "model": ""},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["provider"] == "mock"

    async def test_update_config_openai(self, client: AsyncClient) -> None:
        """Test updating config to OpenAI provider."""
        response = await client.post(
            "/api/v1/config/",
            json={"provider": "openai", "model": "gpt-4"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"

    async def test_update_config_ollama(self, client: AsyncClient) -> None:
        """Test updating config to Ollama provider."""
        response = await client.post(
            "/api/v1/config/",
            json={"provider": "ollama", "model": "llama3.2"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["provider"] == "ollama"
        assert data["model"] == "llama3.2"

    async def test_update_config_invalid_provider(self, client: AsyncClient) -> None:
        """Test updating config with invalid provider."""
        response = await client.post(
            "/api/v1/config/",
            json={"provider": "invalid", "model": ""},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST