from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import ProgramaMateria
from app.repositories.base import TenantScopedRepository


class ProgramaMateriaRepository(TenantScopedRepository[ProgramaMateria]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, ProgramaMateria, tenant_id)
