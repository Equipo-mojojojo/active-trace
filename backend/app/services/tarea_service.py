from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import Tarea
from app.repositories.tarea_repository import TareaRepository
from app.schemas.tareas import TareaCreate, TareaUpdate


class TareaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repository = TareaRepository(db, tenant_id)

    async def create(self, data: TareaCreate) -> Tarea:
        return await self.repository.create(
            asignado_a=data.asignado_a,
            asignado_por=self.user_id,
            descripcion=data.descripcion,
            materia_id=data.materia_id,
            contexto_id=data.contexto_id,
        )

    async def list_all(
        self,
        estado: str | None = None,
        materia_id: UUID | None = None,
        asignado_a: UUID | None = None,
        asignado_por: UUID | None = None,
        q: str | None = None,
    ) -> list[Tarea]:
        return await self.repository.list_filtered(
            estado=estado,
            materia_id=materia_id,
            asignado_a=asignado_a,
            asignado_por=asignado_por,
            q=q,
        )

    async def get(self, tarea_id: UUID) -> Tarea:
        tarea = await self.repository.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return tarea

    async def update(self, tarea_id: UUID, data: TareaUpdate) -> Tarea:
        tarea = await self.repository.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return tarea
        for field, value in update_data.items():
            setattr(tarea, field, value)
        await self.db.flush()
        await self.db.refresh(tarea)
        return tarea

    async def list_mias(self) -> list[Tarea]:
        return await self.repository.list_filtered(asignado_a=self.user_id)
