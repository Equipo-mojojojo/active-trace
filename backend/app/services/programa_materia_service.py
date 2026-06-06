from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import ProgramaMateria
from app.repositories.programa_materia_repository import ProgramaMateriaRepository
from app.schemas.programa_materia import ProgramaMateriaCreate, ProgramaMateriaUpdate


class ProgramaMateriaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = ProgramaMateriaRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[ProgramaMateria]:
        stmt = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == self.tenant_id,
            ProgramaMateria.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(ProgramaMateria.cohorte_id == cohorte_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, programa_id: UUID) -> ProgramaMateria:
        programa = await self.repository.get_by_id(programa_id)
        if programa is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa de materia no encontrado",
            )
        return programa

    async def create(self, data: ProgramaMateriaCreate) -> ProgramaMateria:
        return await self.repository.create(**data.model_dump())

    async def update(
        self, programa_id: UUID, data: ProgramaMateriaUpdate
    ) -> ProgramaMateria:
        programa = await self.get(programa_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return programa
        for field, value in update_data.items():
            setattr(programa, field, value)
        await self.db.flush()
        await self.db.refresh(programa)
        return programa

    async def delete(self, programa_id: UUID) -> None:
        programa = await self.get(programa_id)
        programa.mark_deleted()
        await self.db.flush()
