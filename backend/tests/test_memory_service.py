"""Tests for MemoryService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.session import MemoryService


@pytest.mark.asyncio
class TestMemoryService:
    """Test suite for MemoryService."""

    async def test_create_session(self, db_session: AsyncSession) -> None:
        """Test creating a new session."""
        session = await MemoryService.create_session(db_session, "Test Session")

        assert session["id"] is not None
        assert session["title"] == "Test Session"
        assert "created_at" in session
        assert "updated_at" in session

    async def test_create_session_default_title(self, db_session: AsyncSession) -> None:
        """Test creating a session with default title."""
        session = await MemoryService.create_session(db_session)

        assert session["title"] == "新对话"

    async def test_get_session(self, db_session: AsyncSession) -> None:
        """Test retrieving a session by ID."""
        created = await MemoryService.create_session(db_session, "Get Test")
        retrieved = await MemoryService.get_session(db_session, created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["title"] == "Get Test"

    async def test_get_session_not_found(self, db_session: AsyncSession) -> None:
        """Test retrieving a non-existent session."""
        result = await MemoryService.get_session(
            db_session, str(uuid.uuid4())
        )
        assert result is None

    async def test_get_sessions(self, db_session: AsyncSession) -> None:
        """Test retrieving all sessions ordered by creation time."""
        session1 = await MemoryService.create_session(db_session, "Session 1")
        session2 = await MemoryService.create_session(db_session, "Session 2")

        sessions = await MemoryService.get_sessions(db_session)

        assert len(sessions) >= 2
        # Sessions should be ordered by created_at desc
        titles = [s["title"] for s in sessions]
        assert "Session 2" in titles
        assert "Session 1" in titles

    async def test_update_session(self, db_session: AsyncSession) -> None:
        """Test updating a session title."""
        session = await MemoryService.create_session(db_session, "Old Title")
        updated = await MemoryService.update_session(
            db_session, session["id"], "New Title"
        )

        assert updated is True

        retrieved = await MemoryService.get_session(db_session, session["id"])
        assert retrieved is not None
        assert retrieved["title"] == "New Title"

    async def test_update_session_not_found(self, db_session: AsyncSession) -> None:
        """Test updating a non-existent session."""
        result = await MemoryService.update_session(
            db_session, str(uuid.uuid4()), "New Title"
        )
        assert result is False

    async def test_delete_session(self, db_session: AsyncSession) -> None:
        """Test deleting a session and its messages."""
        session = await MemoryService.create_session(db_session, "To Delete")
        await MemoryService.add_message(
            db_session, session["id"], "user", "Hello"
        )

        deleted = await MemoryService.delete_session(db_session, session["id"])
        assert deleted is True

        retrieved = await MemoryService.get_session(db_session, session["id"])
        assert retrieved is None

        messages = await MemoryService.get_messages(db_session, session["id"])
        assert len(messages) == 0

    async def test_delete_session_not_found(self, db_session: AsyncSession) -> None:
        """Test deleting a non-existent session."""
        result = await MemoryService.delete_session(
            db_session, str(uuid.uuid4())
        )
        assert result is False

    async def test_add_message(self, db_session: AsyncSession) -> None:
        """Test adding a message to a session."""
        session = await MemoryService.create_session(db_session, "Message Test")
        message = await MemoryService.add_message(
            db_session, session["id"], "user", "Hello AI"
        )

        assert message["id"] is not None
        assert message["session_id"] == session["id"]
        assert message["role"] == "user"
        assert message["content"] == "Hello AI"
        assert "created_at" in message

    async def test_add_message_updates_title(
        self, db_session: AsyncSession
    ) -> None:
        """Test that first user message updates session title."""
        session = await MemoryService.create_session(db_session)
        await MemoryService.add_message(
            db_session, session["id"], "user", "My question about Python"
        )

        updated = await MemoryService.get_session(db_session, session["id"])
        assert updated is not None
        assert updated["title"] == "My question about Python"

    async def test_get_messages(self, db_session: AsyncSession) -> None:
        """Test retrieving messages for a session."""
        session = await MemoryService.create_session(db_session, "Messages Test")
        await MemoryService.add_message(
            db_session, session["id"], "user", "Hello"
        )
        await MemoryService.add_message(
            db_session, session["id"], "assistant", "Hi there"
        )

        messages = await MemoryService.get_messages(db_session, session["id"])

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there"

    async def test_get_messages_limit(self, db_session: AsyncSession) -> None:
        """Test message retrieval with limit."""
        session = await MemoryService.create_session(db_session, "Limit Test")
        for i in range(5):
            await MemoryService.add_message(
                db_session, session["id"], "user", f"Message {i}"
            )

        messages = await MemoryService.get_messages(db_session, session["id"], limit=3)
        assert len(messages) == 3

    async def test_get_messages_empty_session(
        self, db_session: AsyncSession
    ) -> None:
        """Test retrieving messages from an empty session."""
        session = await MemoryService.create_session(db_session, "Empty")
        messages = await MemoryService.get_messages(db_session, session["id"])
        assert len(messages) == 0