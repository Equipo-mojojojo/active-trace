from __future__ import annotations

from app.core.security import decode_token
from tests.conftest import create_test_tenant, create_test_user


async def test_login_success_and_identity_comes_only_from_token(client, db_session):
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="admin@example.com",
        roles=["ADMIN", "COORDINADOR"],
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["requires_two_factor"] is False

    payload = decode_token(data["access_token"], expected_type="access")
    assert payload["sub"] == str(user.id)
    assert payload["tenant_id"] == str(tenant.id)
    assert payload["roles"] == ["ADMIN", "COORDINADOR"]
    assert "permissions" not in payload

    me_response = client.get(
        "/api/auth/me?user_id=spoofed&tenant_id=spoofed",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "roles": ["ADMIN", "COORDINADOR"],
        "email": "admin@example.com",
    }


async def test_login_rejects_invalid_credentials(client, db_session):
    tenant = await create_test_tenant(db_session)
    await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="teacher@example.com",
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "teacher@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
