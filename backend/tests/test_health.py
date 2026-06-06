from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint_reports_application_and_database_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_endpoint_reports_database_down_without_crashing(monkeypatch):
    from app.core.config import get_settings
    from tests.conftest import configure_settings_environment

    down_database_url = "postgresql+asyncpg://invalid:invalid@127.0.0.1:1/invalid_db"
    configure_settings_environment(monkeypatch, down_database_url)
    get_settings.cache_clear()

    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "down"}
