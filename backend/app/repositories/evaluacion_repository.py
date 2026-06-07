from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion
from app.repositories.base import TenantScopedRepository


class EvaluacionRepository(TenantScopedRepository[Evaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Evaluacion, tenant_id)
