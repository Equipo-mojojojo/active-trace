from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.repositories.base import TenantScopedRepository


class CarreraRepository(TenantScopedRepository[Carrera]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Carrera, tenant_id)
