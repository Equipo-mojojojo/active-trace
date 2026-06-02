from __future__ import annotations

from fastapi.testclient import TestClient


def test_app_starts_successfully(monkeypatch, test_database_url):
    from app.core.config import get_settings
    from tests.conftest import configure_settings_environment

    configure_settings_environment(monkeypatch, test_database_url)
    get_settings.cache_clear()

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
