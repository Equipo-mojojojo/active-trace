from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.enums import EstadoEncuentro
from app.repositories.instancia_encuentro_repository import (
    InstanciaEncuentroRepository,
)
from app.schemas.encuentros import (
    InstanciaEncuentroCreate,
    InstanciaEncuentroUpdate,
)


class InstanciaEncuentroService:
    """Service for managing individual encounter instances."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = InstanciaEncuentroRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(
        self,
        materia_id: UUID | None = None,
        slot_id: UUID | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        estado: str | None = None,
    ) -> list[InstanciaEncuentro]:
        stmt = select(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == self.tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        )

        if materia_id is not None:
            stmt = stmt.where(InstanciaEncuentro.materia_id == materia_id)
        if slot_id is not None:
            stmt = stmt.where(InstanciaEncuentro.slot_id == slot_id)
        if desde is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha >= desde)
        if hasta is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha <= hasta)
        if estado is not None:
            stmt = stmt.where(InstanciaEncuentro.estado == estado)

        stmt = stmt.order_by(InstanciaEncuentro.fecha, InstanciaEncuentro.hora)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, instancia_id: UUID) -> InstanciaEncuentro:
        instancia = await self.repository.get_by_id(instancia_id)
        if instancia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia de encuentro no encontrada",
            )
        return instancia

    async def create(
        self, data: InstanciaEncuentroCreate
    ) -> InstanciaEncuentro:
        return await self.repository.create(**data.model_dump())

    async def update(
        self, instancia_id: UUID, data: InstanciaEncuentroUpdate
    ) -> InstanciaEncuentro:
        instancia = await self.get(instancia_id)

        update_data = data.model_dump(exclude_unset=True)

        # Validación: video_url solo si estado es Realizado
        if "video_url" in update_data and update_data["video_url"] is not None:
            nuevo_estado = update_data.get("estado", instancia.estado)
            if nuevo_estado != EstadoEncuentro.REALIZADO:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="video_url solo puede establecerse cuando el estado es Realizado",
                )

        if not update_data:
            return instancia

        for field, value in update_data.items():
            setattr(instancia, field, value)

        await self.db.flush()
        await self.db.refresh(instancia)
        return instancia

    async def list_by_materia(
        self, materia_id: UUID
    ) -> list[InstanciaEncuentro]:
        """List active (not cancelled) instances for a materia, ordered by date."""
        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.tenant_id == self.tenant_id,
                InstanciaEncuentro.materia_id == materia_id,
                InstanciaEncuentro.deleted_at.is_(None),
                InstanciaEncuentro.estado != EstadoEncuentro.CANCELADO,
            )
            .order_by(InstanciaEncuentro.fecha, InstanciaEncuentro.hora)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
