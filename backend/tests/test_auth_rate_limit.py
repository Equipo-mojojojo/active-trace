from __future__ import annotations

from tests.conftest import create_test_tenant, create_test_user


async def test_login_rate_limit_and_anonymous_access_restriction(client, db_session):
    tenant = await create_test_tenant(db_session)
    await create_test_user(db_session, tenant_id=tenant.id, email="limit@example.com")

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "limit@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    limited_response = client.post(
        "/api/v1/auth/login",
        json={"email": "limit@example.com", "password": "wrong-password"},
    )

    assert limited_response.status_code == 429

    anonymous_me_response = client.get("/api/v1/auth/me")
    assert anonymous_me_response.status_code == 401
