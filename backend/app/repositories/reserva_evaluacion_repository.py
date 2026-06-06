from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reserva_evaluacion import ReservaEvaluacion
from app.repositories.base import TenantScopedRepository


class ReservaEvaluacionRepository(TenantScopedRepository[ReservaEvaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, ReservaEvaluacion, tenant_id)
