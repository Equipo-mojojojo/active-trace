from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TipoEvaluacion
from app.models.fecha_academica import FechaAcademica
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.schemas.fecha_academica import FechaAcademicaCreate, FechaAcademicaUpdate


class FechaAcademicaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = FechaAcademicaRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        tipo: TipoEvaluacion | None = None,
    ) -> list[FechaAcademica]:
        stmt = select(FechaAcademica).where(
            FechaAcademica.tenant_id == self.tenant_id,
            FechaAcademica.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(FechaAcademica.cohorte_id == cohorte_id)
        if tipo is not None:
            stmt = stmt.where(FechaAcademica.tipo == tipo)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, fecha_id: UUID) -> FechaAcademica:
        fecha = await self.repository.get_by_id(fecha_id)
        if fecha is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha académica no encontrada",
            )
        return fecha

    async def create(self, data: FechaAcademicaCreate) -> FechaAcademica:
        return await self.repository.create(**data.model_dump())

    async def update(
        self, fecha_id: UUID, data: FechaAcademicaUpdate
    ) -> FechaAcademica:
        fecha = await self.get(fecha_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return fecha
        for field, value in update_data.items():
            setattr(fecha, field, value)
        await self.db.flush()
        await self.db.refresh(fecha)
        return fecha

    async def delete(self, fecha_id: UUID) -> None:
        fecha = await self.get(fecha_id)
        fecha.mark_deleted()
        await self.db.flush()
