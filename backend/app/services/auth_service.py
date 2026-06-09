from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from app.core.security import (
    build_email_lookup,
    build_totp_uri,
    create_access_token,
    create_two_factor_challenge_token,
    decode_token,
    hash_password,
    verify_password,
    verify_totp_code,
)
from app.repositories.auth_repository import AuthRepository
from app.repositories.user_repository import UserRepository


class AuthError(ValueError):
    pass


class RateLimitExceededError(ValueError):
    pass


@dataclass(slots=True)
class AuthenticationResult:
    access_token: str | None
    refresh_token: str | None
    expires_in: int | None
    requires_two_factor: bool = False
    challenge_token: str | None = None
    # User context — populated on successful auth, None when 2FA pending
    user_id: str | None = None
    user_full_name: str | None = None
    user_email: str | None = None
    user_tenant_id: str | None = None
    user_roles: list = field(default_factory=list)


class AuthService:
    def __init__(
        self, user_repository: UserRepository, auth_repository: AuthRepository
    ):
        self.user_repository = user_repository
        self.auth_repository = auth_repository

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str | None,
    ) -> AuthenticationResult:
        email_lookup = build_email_lookup(email)
        failed_attempts = await self.auth_repository.count_recent_failed_attempts(
            email_lookup=email_lookup,
            ip_address=ip_address,
        )

        from app.core.config import get_settings

        settings = get_settings()
        if failed_attempts >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
            raise RateLimitExceededError("Too many login attempts")

        user = await self.user_repository.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            await self.auth_repository.record_login_attempt(
                email_lookup=email_lookup,
                ip_address=ip_address,
                was_successful=False,
            )
            await self.auth_repository.session.commit()
            raise AuthError("Invalid credentials")

        await self.auth_repository.record_login_attempt(
            email_lookup=email_lookup,
            ip_address=ip_address,
            was_successful=True,
        )

        if user.two_factor_enabled:
            challenge_token = create_two_factor_challenge_token(
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                roles=list(user.roles),
            )
            return AuthenticationResult(
                access_token=None,
                refresh_token=None,
                expires_in=None,
                requires_two_factor=True,
                challenge_token=challenge_token,
            )

        return await self._create_session_tokens(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def refresh(self, *, refresh_token: str) -> AuthenticationResult:
        stored_refresh_token = await self.auth_repository.get_refresh_token(
            refresh_token
        )
        if stored_refresh_token is None:
            raise AuthError("Refresh token is invalid")

        auth_session = await self.auth_repository.get_auth_session(
            stored_refresh_token.auth_session_id
        )
        if auth_session is None or auth_session.revoked_at is not None:
            raise AuthError("Session is no longer active")

        if (
            stored_refresh_token.revoked_at is not None
            or stored_refresh_token.used_at is not None
        ):
            await self.auth_repository.revoke_session(auth_session)
            raise AuthError("Refresh token reuse detected")

        if stored_refresh_token.expires_at <= datetime.now(UTC):
            await self.auth_repository.revoke_session(auth_session)
            raise AuthError("Refresh token expired")

        user = await self.user_repository.get_authenticated_user(
            user_id=str(stored_refresh_token.user_id),
            tenant_id=str(stored_refresh_token.tenant_id),
        )
        if user is None or not user.is_active:
            await self.auth_repository.revoke_session(auth_session)
            raise AuthError("User is not active")

        await self.auth_repository.mark_refresh_token_used(stored_refresh_token)
        return await self._create_session_tokens(
            user=user,
            ip_address=stored_refresh_token.ip_address,
            user_agent=stored_refresh_token.user_agent,
            existing_session=auth_session,
        )

    async def logout(self, *, current_user, refresh_token: str) -> None:
        stored_refresh_token = await self.auth_repository.get_refresh_token(
            refresh_token
        )
        if (
            stored_refresh_token is None
            or stored_refresh_token.user_id != current_user.id
        ):
            raise AuthError("Refresh token does not belong to current user")

        auth_session = await self.auth_repository.get_auth_session(
            stored_refresh_token.auth_session_id
        )
        if auth_session is None:
            raise AuthError("Session not found")

        await self.auth_repository.revoke_session(auth_session)

    async def forgot_password(self, *, email: str) -> None:
        user = await self.user_repository.get_by_email(email)
        if user is None or not user.is_active:
            return

        await self.auth_repository.create_password_reset_token(user=user)

    async def reset_password(self, *, token: str, new_password: str) -> None:
        password_reset_token = await self.auth_repository.get_password_reset_token(
            token
        )
        if password_reset_token is None:
            raise AuthError("Reset token is invalid")

        if (
            password_reset_token.used_at is not None
            or password_reset_token.revoked_at is not None
        ):
            raise AuthError("Reset token is no longer valid")

        if password_reset_token.expires_at <= datetime.now(UTC):
            raise AuthError("Reset token expired")

        user = await self.user_repository.get_authenticated_user(
            user_id=str(password_reset_token.user_id),
            tenant_id=str(password_reset_token.tenant_id),
        )
        if user is None:
            raise AuthError("User not found")

        user.password_hash = hash_password(new_password)
        await self.auth_repository.mark_password_reset_token_used(password_reset_token)
        await self.auth_repository.revoke_user_sessions(user_id=user.id)

    async def begin_two_factor_enrollment(self, *, current_user) -> tuple[str, str]:
        from app.core.security import generate_totp_secret

        secret = generate_totp_secret()
        current_user.totp_secret = secret
        current_user.two_factor_enabled = False
        await self.user_repository.session.flush()

        provisioning_uri = build_totp_uri(secret, current_user.email)
        return secret, provisioning_uri

    async def enable_two_factor(self, *, current_user, code: str) -> None:
        if current_user.totp_secret is None or not verify_totp_code(
            current_user.totp_secret, code
        ):
            raise AuthError("Two-factor code is invalid")

        current_user.two_factor_enabled = True
        await self.user_repository.session.flush()

    async def verify_two_factor_login(
        self,
        *,
        challenge_token: str,
        code: str,
        ip_address: str,
        user_agent: str | None,
    ) -> AuthenticationResult:
        payload = decode_token(challenge_token, expected_type="two_factor")
        user = await self.user_repository.get_authenticated_user(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
        )
        if (
            user is None
            or not user.is_active
            or not user.two_factor_enabled
            or user.totp_secret is None
        ):
            raise AuthError("Two-factor authentication is not available")

        if not verify_totp_code(user.totp_secret, code):
            raise AuthError("Two-factor code is invalid")

        return await self._create_session_tokens(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _create_session_tokens(
        self,
        *,
        user,
        ip_address: str,
        user_agent: str | None,
        existing_session=None,
    ) -> AuthenticationResult:
        from app.core.config import get_settings

        settings = get_settings()
        auth_session = (
            existing_session
            or await self.auth_repository.create_auth_session(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        refresh_token = await self.auth_repository.issue_refresh_token(
            auth_session=auth_session,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            roles=list(user.roles),
        )
        return AuthenticationResult(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            user_full_name=user.full_name,
            user_email=user.email,
            user_tenant_id=str(user.tenant_id),
            user_roles=list(user.roles),
        )
