from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion
from app.models.enums import EstadoEvaluacion
from app.models.turno_evaluacion import TurnoEvaluacion
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.turno_evaluacion_repository import (
    TurnoEvaluacionRepository,
)
from app.schemas.evaluaciones import EvaluacionCreate, EvaluacionUpdate


class EvaluacionService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = EvaluacionRepository(db, tenant_id)
        self.turno_repo = TurnoEvaluacionRepository(db, tenant_id)

    async def create(self, data: EvaluacionCreate) -> Evaluacion:
        turnos_data = data.turnos
        create_data = data.model_dump(exclude={"turnos"})
        evaluacion = await self.repository.create(**create_data)

        for t in turnos_data:
            await self.turno_repo.create(
                evaluacion_id=evaluacion.id,
                **t.model_dump(),
            )

        await self.db.flush()
        await self.db.refresh(evaluacion)
        return evaluacion

    async def list(self, materia_id: UUID | None = None) -> list[Evaluacion]:
        stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(Evaluacion.materia_id == materia_id)
        stmt = stmt.order_by(Evaluacion.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, evaluacion_id: UUID) -> Evaluacion:
        evaluacion = await self.repository.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        stmt = select(TurnoEvaluacion).where(
            TurnoEvaluacion.tenant_id == self.tenant_id,
            TurnoEvaluacion.evaluacion_id == evaluacion_id,
            TurnoEvaluacion.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        evaluacion.turnos = list(result.scalars().all())
        return evaluacion

    async def update(self, evaluacion_id: UUID, data: EvaluacionUpdate) -> Evaluacion:
        evaluacion = await self.get(evaluacion_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return evaluacion
        for field, value in update_data.items():
            setattr(evaluacion, field, value)
        await self.db.flush()
        await self.db.refresh(evaluacion)
        return evaluacion

    async def cerrar(self, evaluacion_id: UUID) -> Evaluacion:
        evaluacion = await self.get(evaluacion_id)
        evaluacion.estado = EstadoEvaluacion.CERRADA
        await self.db.flush()
        await self.db.refresh(evaluacion)
        return evaluacion
