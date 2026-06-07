from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.models.enums import AlcanceAviso
from app.models.user import User
from app.models.usuario import Usuario
from app.repositories.acknowledgment_repository import (
    AcknowledgmentRepository,
)
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.avisos import AvisoCreate, AvisoDetailResponse, AvisoUpdate


class AvisoService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = AvisoRepository(db, tenant_id)
        self.ack_repo = AcknowledgmentRepository(db, tenant_id)

    async def create(self, data: AvisoCreate) -> Aviso:
        return await self.repository.create(**data.model_dump())

    async def list_all(self) -> list[Aviso]:
        return await self.repository.list_all()

    async def get(self, aviso_id: UUID) -> AvisoDetailResponse:
        aviso = await self.repository.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        total_acks = await self.ack_repo.count_by_aviso(aviso_id)
        total_visibles = await self._count_usuarios_activos()
        return AvisoDetailResponse(
            **{c.name: getattr(aviso, c.name) for c in aviso.__table__.columns},
            total_acks=total_acks,
            total_visibles=total_visibles,
        )

    async def update(self, aviso_id: UUID, data: AvisoUpdate) -> Aviso:
        aviso = await self.repository.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return aviso
        for field, value in update_data.items():
            setattr(aviso, field, value)
        await self.db.flush()
        await self.db.refresh(aviso)
        return aviso

    async def mis_avisos(self, user: User) -> list[Aviso]:
        now = datetime.now(timezone.utc)
        stmt = select(Aviso).where(
            Aviso.tenant_id == self.tenant_id,
            Aviso.deleted_at.is_(None),
            Aviso.activo.is_(True),
            Aviso.inicio_en <= now,
        )
        stmt = stmt.where(
            (Aviso.fin_en.is_(None)) | (Aviso.fin_en >= now)
        )

        result = await self.db.execute(stmt)
        avisos = list(result.scalars().all())

        materias_usuario = set()
        cohortes_usuario = set()

        asignaciones_stmt = select(Asignacion.materia_id, Asignacion.cohorte_id).where(
            Asignacion.usuario_id == user.id,
            Asignacion.deleted_at.is_(None),
        )
        asig_result = await self.db.execute(asignaciones_stmt)
        for row in asig_result:
            if row.materia_id:
                materias_usuario.add(row.materia_id)
            if row.cohorte_id:
                cohortes_usuario.add(row.cohorte_id)

        filtrados = []
        for aviso in avisos:
            if aviso.alcance == AlcanceAviso.GLOBAL:
                pass
            elif aviso.alcance == AlcanceAviso.POR_MATERIA:
                if aviso.materia_id is None or aviso.materia_id not in materias_usuario:
                    continue
            elif aviso.alcance == AlcanceAviso.POR_COHORTE:
                if aviso.cohorte_id is None or aviso.cohorte_id not in cohortes_usuario:
                    continue
            elif aviso.alcance == AlcanceAviso.POR_ROL:
                if aviso.rol_destino is None or aviso.rol_destino not in (user.roles or []):
                    continue

            if aviso.requiere_ack:
                existing_ack = await self.ack_repo.find_by_aviso_usuario(
                    aviso.id, user.id
                )
                if existing_ack is not None:
                    continue

            filtrados.append(aviso)

        filtrados.sort(key=lambda a: (a.orden, a.created_at or datetime.min))
        return filtrados

    async def _count_usuarios_activos(self) -> int:
        stmt = select(Usuario).where(
            Usuario.tenant_id == self.tenant_id,
            Usuario.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))
