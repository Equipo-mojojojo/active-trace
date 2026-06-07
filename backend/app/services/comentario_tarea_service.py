from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.repositories.comentario_tarea_repository import ComentarioTareaRepository
from app.repositories.tarea_repository import TareaRepository


class ComentarioTareaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repository = ComentarioTareaRepository(db, tenant_id)
        self.tarea_repo = TareaRepository(db, tenant_id)

    async def agregar(self, tarea_id: UUID, texto: str) -> ComentarioTarea:
        tarea = await self.tarea_repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return await self.repository.create(
            tarea_id=tarea_id,
            autor_id=self.user_id,
            texto=texto,
        )

    async def listar(self, tarea_id: UUID) -> list[ComentarioTarea]:
        tarea = await self.tarea_repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return await self.repository.list_by_tarea(tarea_id)
