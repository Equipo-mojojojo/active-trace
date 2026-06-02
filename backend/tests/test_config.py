from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_settings_load_from_valid_environment(monkeypatch):
    from app.core.config import Settings, get_settings

    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test_db"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    monkeypatch.setenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
    get_settings.cache_clear()

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL.endswith("test_db")
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15


def test_settings_fail_when_required_variable_is_missing(monkeypatch):
    from app.core.config import Settings, get_settings

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    monkeypatch.setenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_fail_when_access_token_expiry_is_invalid(monkeypatch):
    from app.core.config import Settings, get_settings

    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test_db"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters")
    monkeypatch.setenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "invalid")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
