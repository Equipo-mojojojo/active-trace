from __future__ import annotations

import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_database_session_executes_select_one(monkeypatch, test_database_url):
    from app.core.config import get_settings
    from app.core.database import dispose_engine, get_session_factory
    from tests.conftest import configure_settings_environment

    configure_settings_environment(monkeypatch, test_database_url)
    get_settings.cache_clear()

    session_factory = get_session_factory()

    async with session_factory() as session:
        result = await session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
    await dispose_engine()


@pytest.mark.asyncio
async def test_get_db_closes_session_when_generator_receives_an_exception(
    monkeypatch, test_database_url
):
    from app.core import dependencies
    from app.core.config import get_settings
    from app.core.dependencies import get_db
    from tests.conftest import configure_settings_environment

    configure_settings_environment(monkeypatch, test_database_url)
    get_settings.cache_clear()

    class TrackingSession:
        def __init__(self) -> None:
            self.closed = False
            self.rolled_back = False

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            self.rolled_back = True

        async def close(self) -> None:
            self.closed = True

    tracking_session = TrackingSession()
    monkeypatch.setattr(
        dependencies, "get_session_factory", lambda: lambda: tracking_session
    )

    generator = get_db()
    session = await anext(generator)

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    assert session is tracking_session
    assert tracking_session.rolled_back is True
    assert tracking_session.closed is True
