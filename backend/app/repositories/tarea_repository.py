from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import Tarea
from app.repositories.base import TenantScopedRepository


class TareaRepository(TenantScopedRepository[Tarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Tarea, tenant_id)

    async def list_filtered(
        self,
        estado: str | None = None,
        materia_id: UUID | None = None,
        asignado_a: UUID | None = None,
        asignado_por: UUID | None = None,
        q: str | None = None,
    ) -> list[Tarea]:
        stmt: Select[tuple[Tarea]] = self._statement()

        if estado is not None:
            stmt = stmt.where(Tarea.estado == estado)
        if materia_id is not None:
            stmt = stmt.where(Tarea.materia_id == materia_id)
        if asignado_a is not None:
            stmt = stmt.where(Tarea.asignado_a == asignado_a)
        if asignado_por is not None:
            stmt = stmt.where(Tarea.asignado_por == asignado_por)
        if q is not None:
            stmt = stmt.where(Tarea.descripcion.ilike(f"%{q}%"))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
