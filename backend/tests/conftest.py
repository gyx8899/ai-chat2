"""Pytest fixtures and configuration."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from starlette.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app

# 使用内存 SQLite 进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory for the test engine."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture
async def db_session(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_session_factory() as session:
        yield session
        # 回滚所有更改，保持测试隔离
        await session.rollback()


@pytest.fixture
async def override_get_db(test_session_factory: async_sessionmaker[AsyncSession]) -> Any:
    """Override the app's get_db dependency to use test database."""
    async def _override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    return _override_get_db


@pytest.fixture
async def test_app(override_get_db, test_engine: AsyncEngine):
    """Create app with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    
    # 确保表已创建
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield app
    
    # 清理：清空所有表数据
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    
    app.dependency_overrides.clear()