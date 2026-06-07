from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.repositories.acknowledgment_repository import (
    AcknowledgmentRepository,
)
from app.repositories.aviso_repository import AvisoRepository


class AcknowledgmentService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = AcknowledgmentRepository(db, tenant_id)
        self.aviso_repo = AvisoRepository(db, tenant_id)

    async def confirmar(self, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso:
        aviso = await self.aviso_repo.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        if not aviso.requiere_ack:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este aviso no requiere acknowledgment",
            )

        existing = await self.repository.find_by_aviso_usuario(aviso_id, usuario_id)
        if existing is not None:
            return existing

        return await self.repository.create(
            aviso_id=aviso_id,
            usuario_id=usuario_id,
        )

    async def count_by_aviso(self, aviso_id: UUID) -> int:
        return await self.repository.count_by_aviso(aviso_id)

    async def has_acknowledged(self, aviso_id: UUID, usuario_id: UUID) -> bool:
        existing = await self.repository.find_by_aviso_usuario(aviso_id, usuario_id)
        return existing is not None
