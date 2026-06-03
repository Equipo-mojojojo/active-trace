from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohorte import Cohorte
from app.repositories.base import TenantScopedRepository


class CohorteRepository(TenantScopedRepository[Cohorte]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Cohorte, tenant_id)

    async def exists_by_carrera_and_nombre(
        self, carrera_id: UUID, nombre: str
    ) -> bool:
        result = await self.session.execute(
            select(Cohorte).where(
                Cohorte.tenant_id == self.tenant_id,
                Cohorte.carrera_id == carrera_id,
                Cohorte.nombre == nombre,
                Cohorte.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None
