"""
AnalisisRepository: Read-only queries for C-11 analysis operations.

No business logic here — only tenant-scoped data fetching.
All analysis computation lives in AnalisisService.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron, VersionPadron
from app.models.asignacion import Asignacion
from app.repositories.base import TenantScopedRepository


class AnalisisRepository(TenantScopedRepository[Calificacion]):
    """Thin read-only repo for analysis queries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Calificacion, tenant_id)

    async def calificaciones_por_materia(self, materia_id: UUID) -> list[Calificacion]:
        stmt = self._statement().where(Calificacion.materia_id == materia_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def entradas_por_materia(self, materia_id: UUID) -> list[EntradaPadron]:
        stmt = (
            select(EntradaPadron)
            .join(VersionPadron, EntradaPadron.version_id == VersionPadron.id)
            .where(EntradaPadron.tenant_id == self.tenant_id)
            .where(EntradaPadron.deleted_at.is_(None))
            .where(VersionPadron.tenant_id == self.tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.activa.is_(True))
            .where(VersionPadron.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        entradas = list(result.scalars().unique().all())
        for entrada in entradas:
            setattr(entrada, "_trace_materia_id", materia_id)
        return entradas

    async def asignaciones_activas_usuario(self, usuario_id: UUID) -> list[Asignacion]:
        """Return active assignments for a given user (for PROFESOR/TUTOR scope)."""
        hoy = date.today()
        stmt = (
            select(Asignacion)
            .where(Asignacion.tenant_id == self.tenant_id)
            .where(Asignacion.usuario_id == usuario_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.fecha_desde <= hoy)
            .where(Asignacion.fecha_hasta >= hoy)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def todas_las_entradas(self) -> list[EntradaPadron]:
        """All active EntradaPadron rows for the tenant (for COORDINADOR/ADMIN monitor)."""
        stmt = (
            select(EntradaPadron, VersionPadron.materia_id)
            .join(VersionPadron, EntradaPadron.version_id == VersionPadron.id)
            .where(EntradaPadron.tenant_id == self.tenant_id)
            .where(EntradaPadron.deleted_at.is_(None))
            .where(VersionPadron.tenant_id == self.tenant_id)
            .where(VersionPadron.activa.is_(True))
            .where(VersionPadron.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        rows: list[EntradaPadron] = []
        for entrada, materia_id in result.all():
            setattr(entrada, "_trace_materia_id", materia_id)
            rows.append(entrada)
        return rows

    async def calificaciones_por_entradas(
        self, entrada_ids: list[UUID]
    ) -> list[Calificacion]:
        if not entrada_ids:
            return []
        stmt = self._statement().where(Calificacion.entrada_padron_id.in_(entrada_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
