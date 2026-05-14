"""Tests for sessions router."""

import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import FastAPI
from app.domain.session import MemoryService
from app.db.models.session import Session as ChatSession


@pytest.fixture
async def client(test_app: FastAPI):
    """Create an async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
class TestSessionsRouter:
    """Test suite for sessions REST API."""

    async def test_get_sessions_empty(self, client: AsyncClient) -> None:
        """Test getting session list returns correct structure."""
        response = await client.get("/api/v1/sessions/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    async def test_create_session(self, client: AsyncClient) -> None:
        """Test creating a new session."""
        response = await client.post(
            "/api/v1/sessions/",
            json={"title": "Test Session"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Session"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_session_default_title(
        self, client: AsyncClient
    ) -> None:
        """Test creating a session with default title."""
        response = await client.post("/api/v1/sessions/", json={})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "新对话"

    async def test_get_session(self, client: AsyncClient) -> None:
        """Test getting a specific session."""
        created = await client.post(
            "/api/v1/sessions/",
            json={"title": "Get Test"},
        )
        session_id = created.json()["id"]

        response = await client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "Get Test"

    async def test_get_session_not_found(self, client: AsyncClient) -> None:
        """Test getting a non-existent session."""
        response = await client.get("/api/v1/sessions/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_session(self, client: AsyncClient) -> None:
        """Test updating a session title."""
        created = await client.post(
            "/api/v1/sessions/",
            json={"title": "Old Title"},
        )
        session_id = created.json()["id"]

        response = await client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"title": "New Title"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Title"

    async def test_update_session_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent session."""
        response = await client.patch(
            "/api/v1/sessions/non-existent-id",
            json={"title": "New Title"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_session(self, client: AsyncClient) -> None:
        """Test deleting a session."""
        created = await client.post(
            "/api/v1/sessions/",
            json={"title": "To Delete"},
        )
        session_id = created.json()["id"]

        response = await client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_session_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent session."""
        response = await client.delete("/api/v1/sessions/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_messages(self, client: AsyncClient) -> None:
        """Test getting messages for a session."""
        created = await client.post(
            "/api/v1/sessions/",
            json={"title": "Messages Test"},
        )
        session_id = created.json()["id"]

        response = await client.get(f"/api/v1/sessions/{session_id}/messages")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["messages"] == []
        assert data["total"] == 0

    async def test_get_messages_with_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting messages with data."""
        session = await MemoryService.create_session(db_session, "With Messages")
        await MemoryService.add_message(
            db_session, session["id"], "user", "Hello"
        )
        await MemoryService.add_message(
            db_session,
            session["id"],
            "assistant",
            "Hi!",
            metadata={"prompt_id": "default", "model_id": "mock"},
        )

        response = await client.get(f"/api/v1/sessions/{session['id']}/messages")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["total"] == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["msg_metadata"] is None
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["msg_metadata"] == {"prompt_id": "default", "model_id": "mock"}

    async def test_get_messages_session_not_found(
        self, client: AsyncClient
    ) -> None:
        """Test getting messages for non-existent session."""
        response = await client.get("/api/v1/sessions/non-existent/messages")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ─────────────────────────────────────────────────────────────
    # prompt_type 相关
    # ─────────────────────────────────────────────────────────────

    async def test_create_session_with_prompt_type(
        self, client: AsyncClient
    ) -> None:
        """Test creating a session with prompt_type."""
        response = await client.post(
            "/api/v1/sessions/",
            json={"title": "Frontend Chat", "prompt_type": "frontendAI"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["prompt_type"] == "frontendAI"

    async def test_create_session_without_prompt_type(
        self, client: AsyncClient
    ) -> None:
        """Test creating a session without prompt_type (None)."""
        response = await client.post(
            "/api/v1/sessions/",
            json={"title": "Old Session"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["prompt_type"] is None

    async def test_get_session_includes_prompt_type(
        self, client: AsyncClient
    ) -> None:
        """Test getting a session includes prompt_type in response."""
        created = await client.post(
            "/api/v1/sessions/",
            json={"title": "Test", "prompt_type": "backendAI"},
        )
        session_id = created.json()["id"]
        response = await client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["prompt_type"] == "backendAI"

    async def test_list_sessions_filter_by_prompt_type(
        self, client: AsyncClient
    ) -> None:
        """Test listing sessions with prompt_type filter."""
        # Create sessions with different prompt_types
        await client.post(
            "/api/v1/sessions/",
            json={"title": "Session A", "prompt_type": "frontendAI"},
        )
        await client.post(
            "/api/v1/sessions/",
            json={"title": "Session B", "prompt_type": "backendAI"},
        )

        # Filter by frontendAI
        response = await client.get("/api/v1/sessions/?prompt_type=frontendAI")
        assert response.status_code == status.HTTP_200_OK
        sessions = response.json()["sessions"]
        # All returned sessions should have prompt_type == frontendAI
        for s in sessions:
            assert s["prompt_type"] == "frontendAI"

    async def test_list_default_type_includes_null(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test: default type list includes NULL old sessions."""
        # Create old session with NULL prompt_type (via direct DB)
        old_session = ChatSession(title="Old NULL Session", prompt_type=None)
        db_session.add(old_session)
        await db_session.commit()
        await db_session.refresh(old_session)
        old_id = str(old_session.id)

        # Create new session with default_type
        await client.post(
            "/api/v1/sessions/",
            json={"title": "New Default", "prompt_type": "default"},
        )

        # List with default type
        response = await client.get("/api/v1/sessions/?prompt_type=default")
        assert response.status_code == status.HTTP_200_OK
        sessions = response.json()["sessions"]
        ids = [s["id"] for s in sessions]

        # NULL old session should be visible under default type
        assert old_id in ids

        # List with non-default type (frontendAI) should NOT include NULL
        response2 = await client.get("/api/v1/sessions/?prompt_type=frontendAI")
        assert response2.status_code == status.HTTP_200_OK
        sessions2 = response2.json()["sessions"]
        ids2 = [s["id"] for s in sessions2]
        assert old_id not in ids2
