from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convocado import Convocado
from app.models.evaluacion import Evaluacion
from app.models.enums import EstadoEvaluacion, EstadoReserva
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.turno_evaluacion import TurnoEvaluacion
from app.repositories.reserva_evaluacion_repository import (
    ReservaEvaluacionRepository,
)
from app.repositories.turno_evaluacion_repository import (
    TurnoEvaluacionRepository,
)


class ReservaService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = ReservaEvaluacionRepository(db, tenant_id)
        self.turno_repo = TurnoEvaluacionRepository(db, tenant_id)

    async def reservar(
        self, evaluacion_id: UUID, alumno_id: UUID, turno_id: UUID
    ) -> ReservaEvaluacion:
        evaluacion_stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.id == evaluacion_id,
            Evaluacion.deleted_at.is_(None),
        )
        evaluacion = (
            await self.db.execute(evaluacion_stmt)
        ).scalar_one_or_none()
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        if evaluacion.estado == EstadoEvaluacion.CERRADA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La convocatoria está cerrada",
            )

        turno = await self.turno_repo.get_by_id(turno_id)
        if turno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado",
            )

        convocado_stmt = select(Convocado).where(
            Convocado.tenant_id == self.tenant_id,
            Convocado.evaluacion_id == evaluacion_id,
            Convocado.alumno_id == alumno_id,
            Convocado.deleted_at.is_(None),
        )
        convocado = (
            await self.db.execute(convocado_stmt)
        ).scalar_one_or_none()
        if convocado is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El alumno no está convocado a esta evaluación",
            )

        reserva_existente_stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        reserva_existente = (
            await self.db.execute(reserva_existente_stmt)
        ).scalar_one_or_none()
        if reserva_existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El alumno ya tiene una reserva activa",
            )

        count_stmt = select(func.count()).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.turno_id == turno_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        count = (await self.db.execute(count_stmt)).scalar()
        if count >= turno.max_cupo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El turno no tiene cupo disponible",
            )

        return await self.repository.create(
            turno_id=turno_id,
            alumno_id=alumno_id,
            estado=EstadoReserva.ACTIVA,
        )

    async def cancelar(self, reserva_id: UUID, alumno_id: UUID) -> None:
        reserva = await self.repository.get_by_id(reserva_id)
        if reserva is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada",
            )
        if reserva.alumno_id != alumno_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el dueño de la reserva puede cancelarla",
            )
        if reserva.estado != EstadoReserva.ACTIVA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La reserva ya está cancelada",
            )
        reserva.estado = EstadoReserva.CANCELADA
        await self.db.flush()

    async def listar_por_evaluacion(
        self, evaluacion_id: UUID
    ) -> list[ReservaEvaluacion]:
        stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        turnos_stmt = select(TurnoEvaluacion.id).where(
            TurnoEvaluacion.tenant_id == self.tenant_id,
            TurnoEvaluacion.evaluacion_id == evaluacion_id,
            TurnoEvaluacion.deleted_at.is_(None),
        )
        turnos = (await self.db.execute(turnos_stmt)).scalars().all()
        stmt = stmt.where(ReservaEvaluacion.turno_id.in_(turnos))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def listar_mis_reservas(
        self, alumno_id: UUID
    ) -> list[ReservaEvaluacion]:
        stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.deleted_at.is_(None),
        ).order_by(ReservaEvaluacion.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
