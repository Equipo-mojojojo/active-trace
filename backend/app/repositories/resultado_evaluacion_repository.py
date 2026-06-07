from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.repositories.base import TenantScopedRepository


class ResultadoEvaluacionRepository(TenantScopedRepository[ResultadoEvaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, ResultadoEvaluacion, tenant_id)
