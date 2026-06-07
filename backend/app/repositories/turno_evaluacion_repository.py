from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.turno_evaluacion import TurnoEvaluacion
from app.repositories.base import TenantScopedRepository


class TurnoEvaluacionRepository(TenantScopedRepository[TurnoEvaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, TurnoEvaluacion, tenant_id)
