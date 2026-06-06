from __future__ import annotations

from sqlalchemy import select

from app.models.password_reset_token import PasswordResetToken
from tests.conftest import create_test_tenant, create_test_user


async def test_password_recovery_uses_single_use_reset_token(client, db_session):
    tenant = await create_test_tenant(db_session)
    await create_test_user(db_session, tenant_id=tenant.id, email="recover@example.com")

    forgot_response = client.post(
        "/api/auth/forgot",
        json={"email": "recover@example.com"},
    )

    assert forgot_response.status_code == 200

    stored_token = (
        await db_session.execute(
            select(PasswordResetToken).order_by(PasswordResetToken.created_at.desc())
        )
    ).scalar_one()

    reset_response = client.post(
        "/api/auth/reset",
        json={"token": stored_token.token_value, "new_password": "NewPassword123!"},
    )

    assert reset_response.status_code == 200

    reused_response = client.post(
        "/api/auth/reset",
        json={"token": stored_token.token_value, "new_password": "AnotherPassword123!"},
    )

    assert reused_response.status_code == 400

    old_login = client.post(
        "/api/auth/login",
        json={"email": "recover@example.com", "password": "Password123!"},
    )
    new_login = client.post(
        "/api/auth/login",
        json={"email": "recover@example.com", "password": "NewPassword123!"},
    )

    assert old_login.status_code == 401
    assert new_login.status_code == 200
