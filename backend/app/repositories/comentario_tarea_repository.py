from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.repositories.base import TenantScopedRepository


class ComentarioTareaRepository(TenantScopedRepository[ComentarioTarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, ComentarioTarea, tenant_id)

    async def list_by_tarea(self, tarea_id: UUID) -> list[ComentarioTarea]:
        stmt = self._statement().where(
            ComentarioTarea.tarea_id == tarea_id
        ).order_by(ComentarioTarea.creado_at.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
