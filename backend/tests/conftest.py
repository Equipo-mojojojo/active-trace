from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Activate PII redaction on ALL loggers for every test.
# Unlike handlers, logging.Filter does NOT propagate through the logger
# hierarchy — it must be installed on every logger individually.
from app.core.logging import install_pii_filter

install_pii_filter()

# ---------------------------------------------------------------------------
# Session-level env setup — runs at import time, BEFORE any test collection
# so that models importing get_settings() have the right env vars.
# ---------------------------------------------------------------------------
_test_db_url = os.getenv("TEST_DATABASE_URL")
if _test_db_url:
    os.environ.setdefault("DATABASE_URL", _test_db_url)
    os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    os.environ.setdefault("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")
    os.environ.setdefault("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
    os.environ.setdefault("TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES", "5")
    os.environ.setdefault("TOTP_ISSUER", "activia-trace-test")
    os.environ.setdefault("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5")
    os.environ.setdefault("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
    os.environ.setdefault("OTEL_ENABLED", "false")


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL no est\u00e1 configurada")
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


# ---------------------------------------------------------------------------
# Session-scoped engine — create_all happens ONLY ONCE per test session.
# This is the main performance improvement: 1.5s/test → 0.01s/test for setup.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Session-scoped engine. Creates the full schema ONCE, drops at session end."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL no est\u00e1 configurada")

    from app.core.database import Base
    import app.models  # noqa: F401
    import tests.support_models  # noqa: F401

    eng = create_async_engine(database_url, poolclass=NullPool)

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    Function-scoped session.

    Key performance difference vs the old version:
      Old: engine drop_all() + create_all() per test   → ≈1.5s/test
      New: table.delete() on all tables per test         → ≈0.01s/test

    Tables are created ONCE by the session-scoped ``engine`` fixture.
    Each test cleans the DB at the start via DELETE in reverse-dependency
    order. No wrapping transaction — the test manages its own commits
    and rollbacks normally (important for tests that do both).
    """
    from app.core.database import Base

    # Clean all data in reverse FK order — fast DELETE, no schema changes
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    async with engine.connect() as conn:
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


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
