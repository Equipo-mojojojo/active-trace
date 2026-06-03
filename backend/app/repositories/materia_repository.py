from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.materia import Materia
from app.repositories.base import TenantScopedRepository


class MateriaRepository(TenantScopedRepository[Materia]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Materia, tenant_id)
