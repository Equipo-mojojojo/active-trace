from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_opaque_token, hash_opaque_token
from app.models.auth_login_attempt import AuthLoginAttempt
from app.models.auth_session import AuthSession
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def record_login_attempt(
        self, *, email_lookup: str, ip_address: str, was_successful: bool
    ) -> None:
        attempt = AuthLoginAttempt(
            email_lookup=email_lookup,
            ip_address=ip_address,
            was_successful=was_successful,
        )
        self.session.add(attempt)
        await self.session.flush()

    async def count_recent_failed_attempts(
        self, *, email_lookup: str, ip_address: str
    ) -> int:
        settings = get_settings()
        window_start = datetime.now(UTC) - timedelta(
            seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
        )
        result = await self.session.execute(
            select(func.count(AuthLoginAttempt.id)).where(
                AuthLoginAttempt.email_lookup == email_lookup,
                AuthLoginAttempt.ip_address == ip_address,
                AuthLoginAttempt.was_successful.is_(False),
                AuthLoginAttempt.created_at >= window_start,
                AuthLoginAttempt.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def create_auth_session(
        self, *, user: User, ip_address: str | None, user_agent: str | None
    ) -> AuthSession:
        auth_session = AuthSession(
            tenant_id=user.tenant_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(auth_session)
        await self.session.flush()
        await self.session.refresh(auth_session)
        return auth_session

    async def issue_refresh_token(
        self,
        *,
        auth_session: AuthSession,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
    ) -> str:
        settings = get_settings()
        raw_token = create_opaque_token()
        refresh_token = RefreshToken(
            tenant_id=user.tenant_id,
            auth_session_id=auth_session.id,
            user_id=user.id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(refresh_token)
        auth_session.last_rotated_at = datetime.now(UTC)
        await self.session.flush()
        return raw_token

    async def get_refresh_token(self, raw_token: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_opaque_token(raw_token),
                RefreshToken.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_auth_session(self, auth_session_id: UUID) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSession).where(
                AuthSession.id == auth_session_id, AuthSession.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_refresh_token_used(self, refresh_token: RefreshToken) -> None:
        now = datetime.now(UTC)
        refresh_token.used_at = now
        refresh_token.revoked_at = now
        await self.session.flush()

    async def revoke_session(self, auth_session: AuthSession) -> None:
        now = datetime.now(UTC)
        auth_session.revoked_at = now
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.auth_session_id == auth_session.id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.deleted_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self.session.flush()

    async def create_password_reset_token(self, *, user: User) -> str:
        settings = get_settings()
        raw_token = create_opaque_token()
        password_reset_token = PasswordResetToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_hash=hash_opaque_token(raw_token),
            token_value=raw_token,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
        self.session.add(password_reset_token)
        await self.session.flush()
        return raw_token

    async def get_password_reset_token(
        self, raw_token: str
    ) -> PasswordResetToken | None:
        result = await self.session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hash_opaque_token(raw_token),
                PasswordResetToken.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def mark_password_reset_token_used(
        self, password_reset_token: PasswordResetToken
    ) -> None:
        password_reset_token.used_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_user_sessions(self, *, user_id: UUID) -> None:
        result = await self.session.execute(
            select(AuthSession).where(
                AuthSession.user_id == user_id, AuthSession.deleted_at.is_(None)
            )
        )
        sessions = result.scalars().all()
        for auth_session in sessions:
            await self.revoke_session(auth_session)
