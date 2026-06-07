from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convocado import Convocado
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.enums import EstadoReserva
from app.repositories.convocado_repository import ConvocadoRepository


class ConvocadoService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = ConvocadoRepository(db, tenant_id)

    async def importar(self, evaluacion_id: UUID, alumno_ids: list[UUID]) -> int:
        count = 0
        for alumno_id in alumno_ids:
            existing = await self.repository.get_by_id(None)
            stmt = select(Convocado).where(
                Convocado.tenant_id == self.tenant_id,
                Convocado.evaluacion_id == evaluacion_id,
                Convocado.alumno_id == alumno_id,
                Convocado.deleted_at.is_(None),
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none() is not None:
                continue
            await self.repository.create(
                evaluacion_id=evaluacion_id,
                alumno_id=alumno_id,
            )
            count += 1
        await self.db.flush()
        return count

    async def listar(
        self, evaluacion_id: UUID, q: str | None = None
    ) -> list[Convocado]:
        stmt = select(Convocado).where(
            Convocado.tenant_id == self.tenant_id,
            Convocado.evaluacion_id == evaluacion_id,
            Convocado.deleted_at.is_(None),
        )
        if q:
            stmt = stmt.where(Convocado.alumno_id == UUID(q))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def remover(self, evaluacion_id: UUID, alumno_id: UUID) -> None:
        reserva_stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        reserva_result = await self.db.execute(reserva_stmt)
        if reserva_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede remover un alumno con reserva activa",
            )

        stmt = select(Convocado).where(
            Convocado.tenant_id == self.tenant_id,
            Convocado.evaluacion_id == evaluacion_id,
            Convocado.alumno_id == alumno_id,
            Convocado.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        convocado = result.scalar_one_or_none()
        if convocado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alumno no está convocado a esta evaluación",
            )
        convocado.mark_deleted()
        await self.db.flush()
