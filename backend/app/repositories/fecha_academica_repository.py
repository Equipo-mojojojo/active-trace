from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fecha_academica import FechaAcademica
from app.repositories.base import TenantScopedRepository


class FechaAcademicaRepository(TenantScopedRepository[FechaAcademica]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, FechaAcademica, tenant_id)
