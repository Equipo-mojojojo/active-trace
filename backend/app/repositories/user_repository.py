from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import build_email_lookup
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email_lookup == build_email_lookup(email),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_authenticated_user(self, user_id: str, tenant_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.id == UUID(user_id),
                User.tenant_id == UUID(tenant_id),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        tenant_id: UUID,
        email: str,
        full_name: str,
        password_hash: str,
        roles: list[str],
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email,
            email_lookup=build_email_lookup(email),
            full_name=full_name,
            password_hash=password_hash,
            roles=roles,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
