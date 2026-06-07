from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aviso import Aviso
from app.repositories.base import TenantScopedRepository


class AvisoRepository(TenantScopedRepository[Aviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Aviso, tenant_id)
