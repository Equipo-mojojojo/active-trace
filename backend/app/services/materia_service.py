from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.materia import Materia
from app.repositories.materia_repository import MateriaRepository
from app.schemas.materia import MateriaCreate, MateriaUpdate


class MateriaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = MateriaRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(self) -> list[Materia]:
        return await self.repository.list_all()

    async def get(self, materia_id: UUID) -> Materia:
        materia = await self.repository.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada",
            )
        return materia

    async def create(self, data: MateriaCreate) -> Materia:
        await self._ensure_unique_codigo(data.codigo)
        return await self.repository.create(**data.model_dump())

    async def update(self, materia_id: UUID, data: MateriaUpdate) -> Materia:
        materia = await self.get(materia_id)

        if data.codigo is not None and data.codigo != materia.codigo:
            await self._ensure_unique_codigo(data.codigo, exclude_id=materia_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return materia

        for field, value in update_data.items():
            setattr(materia, field, value)

        await self.db.flush()
        await self.db.refresh(materia)
        return materia

    async def delete(self, materia_id: UUID) -> None:
        materia = await self.get(materia_id)
        materia.mark_deleted()
        await self.db.flush()

    async def _ensure_unique_codigo(
        self, codigo: str, exclude_id: UUID | None = None
    ) -> None:
        stmt = select(Materia).where(
            Materia.tenant_id == self.tenant_id,
            Materia.codigo == codigo,
            Materia.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una materia con ese código",
            )
