from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def initialize_database(settings: Settings | None = None) -> None:
    global _engine, _session_factory

    if _engine is not None and _session_factory is not None:
        return

    resolved_settings = settings or get_settings()
    _engine = create_async_engine(
        resolved_settings.DATABASE_URL,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    initialize_database()
    assert _engine is not None
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    initialize_database()
    assert _session_factory is not None
    return _session_factory


async def dispose_engine() -> None:
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_factory = None
