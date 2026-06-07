from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.base import TenantScopedRepository


class InstanciaEncuentroRepository(TenantScopedRepository[InstanciaEncuentro]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, InstanciaEncuentro, tenant_id)
