from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def configure_settings_environment(
    monkeypatch: pytest.MonkeyPatch, database_url: str
) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    monkeypatch.setenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")
    monkeypatch.setenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES", "5")
    monkeypatch.setenv("TOTP_ISSUER", "activia-trace-test")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("OTEL_ENABLED", "false")


@pytest.fixture
def test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL no está configurada")
    return database_url


@pytest.fixture
def configured_app(monkeypatch: pytest.MonkeyPatch, test_database_url: str):
    from app.core.config import get_settings
    from app.core.database import dispose_engine

    configure_settings_environment(monkeypatch, test_database_url)
    get_settings.cache_clear()

    from app.main import create_app

    application = create_app()
    yield application
    get_settings.cache_clear()

    import asyncio

    asyncio.run(dispose_engine())


@pytest.fixture
def client(configured_app):
    with TestClient(configured_app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def db_session(monkeypatch: pytest.MonkeyPatch, test_database_url: str):
    from app.core.config import get_settings
    from app.core.database import Base
    import app.models  # noqa: F401
    import tests.support_models  # noqa: F401

    configure_settings_environment(monkeypatch, test_database_url)
    get_settings.cache_clear()

    engine = create_async_engine(test_database_url, poolclass=NullPool)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    get_settings.cache_clear()


async def create_test_tenant(
    db_session, *, slug: str = "tenant-a", name: str = "Tenant A"
):
    from app.models.tenant import Tenant

    tenant = Tenant(slug=slug, name=name)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


async def create_test_user(
    db_session,
    *,
    tenant_id: UUID,
    email: str = "user@example.com",
    full_name: str = "Test User",
    password: str = "Password123!",
    roles: list[str] | None = None,
):
    from app.core.security import hash_password
    from app.repositories.user_repository import UserRepository

    repository = UserRepository(db_session)
    user = await repository.create_user(
        tenant_id=tenant_id,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        roles=roles or ["ADMIN"],
    )
    await db_session.commit()
    await db_session.refresh(user)
    return user
