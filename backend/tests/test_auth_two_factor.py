from __future__ import annotations

import pyotp

from tests.conftest import create_test_tenant, create_test_user


async def test_two_factor_enrollment_and_login_challenge_flow(client, db_session):
    tenant = await create_test_tenant(db_session)
    await create_test_user(db_session, tenant_id=tenant.id, email="2fa@example.com")

    login_response = client.post(
        "/api/auth/login",
        json={"email": "2fa@example.com", "password": "Password123!"},
    )
    login_payload = login_response.json()

    enroll_response = client.post(
        "/api/auth/2fa/enroll",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert enroll_response.status_code == 200
    enroll_payload = enroll_response.json()
    totp = pyotp.TOTP(enroll_payload["secret"])

    enable_response = client.post(
        "/api/auth/2fa/enable",
        json={"code": totp.now()},
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )

    assert enable_response.status_code == 200

    second_login = client.post(
        "/api/auth/login",
        json={"email": "2fa@example.com", "password": "Password123!"},
    )

    assert second_login.status_code == 200
    challenge_payload = second_login.json()
    assert challenge_payload["requires_two_factor"] is True
    assert challenge_payload["challenge_token"] is not None
    assert challenge_payload["access_token"] is None

    invalid_verify = client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_payload["challenge_token"],
            "code": "000000",
        },
    )

    assert invalid_verify.status_code == 401

    valid_verify = client.post(
        "/api/auth/2fa/verify",
        json={
            "challenge_token": challenge_payload["challenge_token"],
            "code": totp.now(),
        },
    )

    assert valid_verify.status_code == 200
    assert valid_verify.json()["access_token"] is not None
