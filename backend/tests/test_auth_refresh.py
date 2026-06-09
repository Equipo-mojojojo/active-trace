from __future__ import annotations

from tests.conftest import create_test_tenant, create_test_user


async def test_refresh_rotation_rejects_reuse_and_logout_revokes_session(
    client, db_session
):
    tenant = await create_test_tenant(db_session)
    await create_test_user(db_session, tenant_id=tenant.id, email="refresh@example.com")

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password123!"},
    )
    login_payload = login_response.json()

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    rotated_payload = refresh_response.json()
    assert rotated_payload["refresh_token"] != login_payload["refresh_token"]

    reused_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )

    assert reused_response.status_code == 401
    assert reused_response.json()["detail"] == "Refresh token reuse detected"

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": rotated_payload["refresh_token"]},
        headers={"Authorization": f"Bearer {rotated_payload['access_token']}"},
    )

    assert logout_response.status_code == 204

    revoked_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_payload["refresh_token"]},
    )

    assert revoked_response.status_code == 401
