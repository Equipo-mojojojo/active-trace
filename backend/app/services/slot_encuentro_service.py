from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.instancia_encuentro_repository import (
    InstanciaEncuentroRepository,
)
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.schemas.encuentros import SlotEncuentroCreate, SlotEncuentroUpdate


class SlotEncuentroService:
    """Service for managing slot de encuentro (recurrent and single-date).

    When a recurrent slot is created, all weekly instances are generated
    automatically in the same transaction.
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = SlotEncuentroRepository(db, tenant_id)
        self.instancia_repository = InstanciaEncuentroRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(self) -> list[SlotEncuentro]:
        return await self.repository.list_all()

    async def get(self, slot_id: UUID) -> SlotEncuentro:
        slot = await self.repository.get_by_id(slot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot de encuentro no encontrado",
            )
        return slot

    async def create(self, data: SlotEncuentroCreate) -> SlotEncuentro:
        """Create a slot and generate all its instances in one transaction."""
        slot = await self.repository.create(**data.model_dump())

        await self._generate_instancias(slot)

        await self.db.flush()
        return slot

    async def update(
        self, slot_id: UUID, data: SlotEncuentroUpdate
    ) -> SlotEncuentro:
        slot = await self.get(slot_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return slot

        for field, value in update_data.items():
            setattr(slot, field, value)

        await self.db.flush()
        await self.db.refresh(slot)
        return slot

    async def delete(self, slot_id: UUID) -> None:
        slot = await self.get(slot_id)
        slot.mark_deleted()
        await self.db.flush()

    async def _generate_instancias(self, slot: SlotEncuentro) -> None:
        """Generate InstanciaEncuentro records for a slot."""
        if slot.cant_semanas > 0:
            # Recurrente: genera 1 instancia por semana
            for semana in range(slot.cant_semanas):
                fecha = slot.fecha_inicio + timedelta(weeks=semana)
                await self.instancia_repository.create(
                    slot_id=slot.id,
                    materia_id=slot.materia_id,
                    fecha=fecha,
                    hora=slot.hora,
                    titulo=slot.titulo,
                    meet_url=slot.meet_url,
                )
        elif slot.fecha_unica is not None:
            # Fecha única: genera 1 instancia
            await self.instancia_repository.create(
                slot_id=slot.id,
                materia_id=slot.materia_id,
                fecha=slot.fecha_unica,
                hora=slot.hora,
                titulo=slot.titulo,
                meet_url=slot.meet_url,
            )
