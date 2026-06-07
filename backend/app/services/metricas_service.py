from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convocado import Convocado
from app.models.evaluacion import Evaluacion
from app.models.enums import EstadoReserva
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.turno_evaluacion import TurnoEvaluacion


class MetricasService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def globales(self) -> dict:
        total_convocatorias = (
            await self.db.execute(
                select(func.count(Evaluacion.id)).where(
                    Evaluacion.tenant_id == self.tenant_id,
                    Evaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_convocados = (
            await self.db.execute(
                select(func.count(Convocado.id)).where(
                    Convocado.tenant_id == self.tenant_id,
                    Convocado.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_reservas_activas = (
            await self.db.execute(
                select(func.count(ReservaEvaluacion.id)).where(
                    ReservaEvaluacion.tenant_id == self.tenant_id,
                    ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                    ReservaEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_resultados = (
            await self.db.execute(
                select(func.count(ResultadoEvaluacion.id)).where(
                    ResultadoEvaluacion.tenant_id == self.tenant_id,
                    ResultadoEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_cupos = (
            await self.db.execute(
                select(func.coalesce(func.sum(TurnoEvaluacion.max_cupo), 0)).where(
                    TurnoEvaluacion.tenant_id == self.tenant_id,
                    TurnoEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_reservas = (
            await self.db.execute(
                select(func.count(ReservaEvaluacion.id)).where(
                    ReservaEvaluacion.tenant_id == self.tenant_id,
                    ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                    ReservaEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        total_cupos_libres = total_cupos - total_reservas

        return {
            "total_convocatorias": total_convocatorias,
            "total_convocados": total_convocados,
            "total_reservas_activas": total_reservas_activas,
            "total_resultados": total_resultados,
            "total_cupos_libres": total_cupos_libres,
        }

    async def por_convocatoria(self, evaluacion_id: UUID) -> dict:
        convocados = (
            await self.db.execute(
                select(func.count(Convocado.id)).where(
                    Convocado.tenant_id == self.tenant_id,
                    Convocado.evaluacion_id == evaluacion_id,
                    Convocado.deleted_at.is_(None),
                )
            )
        ).scalar()

        turnos_stmt = select(TurnoEvaluacion.id).where(
            TurnoEvaluacion.tenant_id == self.tenant_id,
            TurnoEvaluacion.evaluacion_id == evaluacion_id,
            TurnoEvaluacion.deleted_at.is_(None),
        )
        turnos = (await self.db.execute(turnos_stmt)).scalars().all()

        total_cupos = 0
        for turno_id in turnos:
            max_cupo = (
                await self.db.execute(
                    select(TurnoEvaluacion.max_cupo).where(TurnoEvaluacion.id == turno_id)
                )
            ).scalar()
            total_cupos += max_cupo or 0

        reservas_activas = 0
        for turno_id in turnos:
            count = (
                await self.db.execute(
                    select(func.count(ReservaEvaluacion.id)).where(
                        ReservaEvaluacion.tenant_id == self.tenant_id,
                        ReservaEvaluacion.turno_id == turno_id,
                        ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                        ReservaEvaluacion.deleted_at.is_(None),
                    )
                )
            ).scalar()
            reservas_activas += count

        cupos_libres = total_cupos - reservas_activas

        resultados_registrados = (
            await self.db.execute(
                select(func.count(ResultadoEvaluacion.id)).where(
                    ResultadoEvaluacion.tenant_id == self.tenant_id,
                    ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                    ResultadoEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar()

        return {
            "convocados": convocados,
            "reservas_activas": reservas_activas,
            "cupos_libres": cupos_libres,
            "resultados_registrados": resultados_registrados,
        }
