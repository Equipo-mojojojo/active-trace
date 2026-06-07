from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.enums import EstadoActivo
from app.repositories.cohorte_repository import CohorteRepository
from app.schemas.cohorte import CohorteCreate, CohorteUpdate


class CohorteService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = CohorteRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(self) -> list[Cohorte]:
        return await self.repository.list_all()

    async def get(self, cohorte_id: UUID) -> Cohorte:
        cohorte = await self.repository.get_by_id(cohorte_id)
        if cohorte is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cohorte no encontrada",
            )
        return cohorte

    async def create(self, data: CohorteCreate) -> Cohorte:
        await self._validate_carrera_activa(data.carrera_id, data.vig_hasta)
        if await self.repository.exists_by_carrera_and_nombre(
            data.carrera_id, data.nombre
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cohorte con ese nombre en la misma carrera",
            )
        return await self.repository.create(**data.model_dump())

    async def update(self, cohorte_id: UUID, data: CohorteUpdate) -> Cohorte:
        cohorte = await self.get(cohorte_id)

        if data.vig_hasta is None and data.vig_hasta != cohorte.vig_hasta:
            await self._validate_carrera_activa(cohorte.carrera_id, None)

        if data.nombre is not None and data.nombre != cohorte.nombre:
            carrera_id = data.carrera_id or cohorte.carrera_id
            if await self.repository.exists_by_carrera_and_nombre(
                carrera_id, data.nombre
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una cohorte con ese nombre en la misma carrera",
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return cohorte

        for field, value in update_data.items():
            setattr(cohorte, field, value)

        await self.db.flush()
        await self.db.refresh(cohorte)
        return cohorte

    async def delete(self, cohorte_id: UUID) -> None:
        cohorte = await self.get(cohorte_id)
        cohorte.mark_deleted()
        await self.db.flush()

    async def _validate_carrera_activa(
        self, carrera_id: UUID, vig_hasta: date | None
    ) -> None:
        result = await self.db.execute(
            select(Carrera).where(
                Carrera.id == carrera_id,
                Carrera.tenant_id == self.tenant_id,
                Carrera.deleted_at.is_(None),
            )
        )
        carrera = result.scalar_one_or_none()
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada",
            )
        if carrera.estado == EstadoActivo.INACTIVA and vig_hasta is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pueden crear cohortes abiertas en carreras inactivas",
            )
