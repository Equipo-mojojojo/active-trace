from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convocado import Convocado
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.repositories.resultado_evaluacion_repository import (
    ResultadoEvaluacionRepository,
)


class ResultadoService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = ResultadoEvaluacionRepository(db, tenant_id)

    async def registrar_o_actualizar(
        self, evaluacion_id: UUID, alumno_id: UUID, nota_final: str | None
    ) -> ResultadoEvaluacion:
        stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self.tenant_id,
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.alumno_id == alumno_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.nota_final = nota_final
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        return await self.repository.create(
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            nota_final=nota_final,
        )

    async def listar(self, evaluacion_id: UUID) -> list[ResultadoEvaluacion]:
        stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self.tenant_id,
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        ).order_by(ResultadoEvaluacion.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def export_csv(self, evaluacion_id: UUID) -> str:
        convocados_stmt = select(Convocado).where(
            Convocado.tenant_id == self.tenant_id,
            Convocado.evaluacion_id == evaluacion_id,
            Convocado.deleted_at.is_(None),
        )
        convocados = (await self.db.execute(convocados_stmt)).scalars().all()

        resultados_stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self.tenant_id,
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        resultados = (await self.db.execute(resultados_stmt)).scalars().all()
        resultado_map = {r.alumno_id: r.nota_final for r in resultados}

        lines = ["alummo_id,nota_final"]
        for c in convocados:
            nota = resultado_map.get(c.alumno_id, "")
            lines.append(f"{c.alumno_id},{nota}")
        return "\n".join(lines)
