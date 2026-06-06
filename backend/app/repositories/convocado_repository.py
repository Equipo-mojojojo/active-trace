from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convocado import Convocado
from app.repositories.base import TenantScopedRepository


class ConvocadoRepository(TenantScopedRepository[Convocado]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Convocado, tenant_id)
