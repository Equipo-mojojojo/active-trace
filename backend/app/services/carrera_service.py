from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.repositories.carrera_repository import CarreraRepository
from app.schemas.carrera import CarreraCreate, CarreraUpdate


class CarreraService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = CarreraRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(self) -> list[Carrera]:
        return await self.repository.list_all()

    async def get(self, carrera_id: UUID) -> Carrera:
        carrera = await self.repository.get_by_id(carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada",
            )
        return carrera

    async def create(self, data: CarreraCreate) -> Carrera:
        await self._ensure_unique_codigo(data.codigo)
        return await self.repository.create(**data.model_dump())

    async def update(self, carrera_id: UUID, data: CarreraUpdate) -> Carrera:
        carrera = await self.get(carrera_id)

        if data.codigo is not None and data.codigo != carrera.codigo:
            await self._ensure_unique_codigo(data.codigo, exclude_id=carrera_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return carrera

        for field, value in update_data.items():
            setattr(carrera, field, value)

        await self.db.flush()
        await self.db.refresh(carrera)
        return carrera

    async def delete(self, carrera_id: UUID) -> None:
        carrera = await self.get(carrera_id)
        carrera.mark_deleted()
        await self.db.flush()

    async def _ensure_unique_codigo(
        self, codigo: str, exclude_id: UUID | None = None
    ) -> None:
        stmt = select(Carrera).where(
            Carrera.tenant_id == self.tenant_id,
            Carrera.codigo == codigo,
            Carrera.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None and (exclude_id is None or existing.id != exclude_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una carrera con ese código",
            )
