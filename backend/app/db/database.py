"""DB 模块 - 数据库配置。

重构自 app/database.py - 支持 PostgreSQL 16 (asyncpg) 和 SQLite (aiosqlite)。
采用 DDD 分层架构，db 层专注于数据持久化。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.settings import settings


def _is_postgresql(url: str) -> bool:
    """判断是否为 PostgreSQL URL。"""
    return url.startswith(("postgresql://", "postgresql+asyncpg://"))


def _is_sqlite(url: str) -> bool:
    """判断是否为 SQLite URL。"""
    return url.startswith(("sqlite://", "sqlite+aiosqlite://"))


def _normalize_db_url(url: str) -> str:
    """归一化数据库 URL，确保使用异步驱动。

    - postgresql:// → postgresql+asyncpg://
    - sqlite:// → sqlite+aiosqlite://
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://") and "aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


# 归一化 URL
_db_url = _normalize_db_url(settings.database.url)
_is_pg = _is_postgresql(_db_url)
_is_sqlite_db = _is_sqlite(_db_url)

# 连接参数（SQLite 需特殊处理）
_connect_args: dict = {}
if _is_sqlite_db:
    _connect_args = {"check_same_thread": False}

# 引擎配置（PostgreSQL 启用连接池，SQLite 使用 NullPool）
_engine_kwargs: dict = {
    "echo": settings.database.echo,
    "future": True,
    "connect_args": _connect_args,
}

if _is_pg:
    _engine_kwargs.update(
        {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
            "pool_pre_ping": settings.database.pool_pre_ping,
            "pool_recycle": 3600,  # 1 小时回收连接
        }
    )
else:
    # SQLite 使用 NullPool 避免连接复用问题
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(_db_url, **_engine_kwargs)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库：创建所有表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接池。"""
    await engine.dispose()


__all__ = [
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
]