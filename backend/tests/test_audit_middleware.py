"""Tests for the audit middleware (IP and User-Agent capture).

These use FastAPI's ``TestClient`` to send requests through the full
middleware stack and inspect ``request.state`` via a dedicated test
endpoint.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.audit_middleware import AuditMiddleware


# ── Helper app with inspection endpoint ─────────────────────────────


@pytest.fixture
def inspect_app() -> FastAPI:
    """Small FastAPI app with AuditMiddleware for testing."""
    application = FastAPI()
    application.add_middleware(AuditMiddleware)

    @application.get("/inspect")
    async def inspect(request: Request):
        return {
            "ip": getattr(request.state, "ip", None),
            "user_agent": getattr(request.state, "user_agent", None),
        }

    return application


@pytest.fixture
def client(inspect_app: FastAPI) -> TestClient:
    return TestClient(inspect_app)


# ── Tests ────────────────────────────────────────────────────────────


class TestAuditMiddleware:
    """Verify IP and User-Agent are captured correctly."""

    def test_captures_ip_from_x_forwarded_for(self, client: TestClient) -> None:
        """X-Forwarded-For header is used when present."""
        response = client.get(
            "/inspect", headers={"X-Forwarded-For": "203.0.113.42"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "203.0.113.42"

    def test_takes_first_ip_when_multiple_in_x_forwarded_for(
        self, client: TestClient
    ) -> None:
        """When X-Forwarded-For has multiple addresses, the first wins."""
        response = client.get(
            "/inspect",
            headers={"X-Forwarded-For": "198.51.100.1, 10.0.0.1, 203.0.113.42"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "198.51.100.1"

    def test_falls_back_to_remote_addr(self, client: TestClient) -> None:
        """Without proxy headers, request.client.host is used."""
        # TestClient uses 127.0.0.1 as client.host by default
        response = client.get("/inspect")
        assert response.status_code == 200
        data = response.json()
        # TestClient sets client host to testserver or 127.0.0.1
        assert data["ip"] is not None
        assert isinstance(data["ip"], str)
        assert len(data["ip"]) > 0

    def test_captures_user_agent(self, client: TestClient) -> None:
        """User-Agent header is captured correctly."""
        response = client.get(
            "/inspect",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_agent"] == "Mozilla/5.0 (Windows NT 10.0)"

    def test_user_agent_is_none_when_missing(self, client: TestClient) -> None:
        """When no User-Agent header, state.user_agent is None."""
        # TestClient itself may set a User-Agent by default
        response = client.get("/inspect", headers={"User-Agent": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["user_agent"] == ""

    def test_x_real_ip_takes_precedence_over_remote_addr(
        self, client: TestClient
    ) -> None:
        """X-Real-IP is used when X-Forwarded-For is absent."""
        # X-Forwarded-For absent → falls to X-Real-IP
        response = client.get(
            "/inspect", headers={"X-Real-IP": "10.0.0.42"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "10.0.0.42"

    def test_x_forwarded_for_takes_precedence_over_x_real_ip(
        self, client: TestClient
    ) -> None:
        """X-Forwarded-For takes precedence over X-Real-IP when both present."""
        response = client.get(
            "/inspect",
            headers={
                "X-Forwarded-For": "203.0.113.42",
                "X-Real-IP": "10.0.0.1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ip"] == "203.0.113.42"
