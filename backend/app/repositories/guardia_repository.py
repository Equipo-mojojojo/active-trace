from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia
from app.repositories.base import TenantScopedRepository


class GuardiaRepository(TenantScopedRepository[Guardia]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Guardia, tenant_id)
