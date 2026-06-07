from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion


class MetricasAuditoriaRepository:
    """Read-only analytics repository over AuditLog and Comunicacion.

    All queries are scoped to tenant_id. Uses SQLAlchemy Core aggregations
    (GROUP BY) rather than ORM mapped objects.
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))

    async def acciones_por_dia(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
    ) -> list[dict]:
        fecha_col = func.date(AuditLog.fecha_hora).label("fecha")
        stmt = (
            select(fecha_col, func.count(AuditLog.id).label("total"))
            .where(AuditLog.tenant_id == self.tenant_id)
            .group_by(fecha_col)
            .order_by(fecha_col)
        )
        if desde:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if materia_id:
            stmt = stmt.where(AuditLog.materia_id == materia_id)

        result = await self.session.execute(stmt)
        return [{"fecha": row.fecha, "total": row.total} for row in result]

    async def estado_comunicaciones(
        self,
        materia_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                Comunicacion.materia_id.label("materia_id"),
                Comunicacion.estado.label("estado"),
                func.count(Comunicacion.id).label("total"),
            )
            .where(Comunicacion.tenant_id == self.tenant_id)
            .where(Comunicacion.deleted_at.is_(None))
            .group_by(Comunicacion.materia_id, Comunicacion.estado)
            .order_by(Comunicacion.materia_id, Comunicacion.estado)
        )
        if materia_id:
            stmt = stmt.where(Comunicacion.materia_id == materia_id)

        result = await self.session.execute(stmt)
        rows = [
            {"materia_id": r.materia_id, "estado": r.estado, "total": r.total}
            for r in result
        ]

        if actor_id:
            rows = [r for r in rows]

        return rows

    async def interacciones_por_docente_materia(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                AuditLog.actor_id,
                AuditLog.materia_id,
                AuditLog.accion,
                func.count(AuditLog.id).label("total"),
            )
            .where(AuditLog.tenant_id == self.tenant_id)
            .group_by(AuditLog.actor_id, AuditLog.materia_id, AuditLog.accion)
            .order_by(func.count(AuditLog.id).desc())
        )
        if desde:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await self.session.execute(stmt)
        return [
            {
                "actor_id": r.actor_id,
                "materia_id": r.materia_id,
                "accion": r.accion,
                "total": r.total,
            }
            for r in result
        ]

    async def ultimas_acciones(
        self,
        limite: int = 200,
        materia_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == self.tenant_id)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limite)
        )
        if materia_id:
            stmt = stmt.where(AuditLog.materia_id == materia_id)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
