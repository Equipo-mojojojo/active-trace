from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion
from app.models.enums import EstadoComunicacion
from app.repositories.base import TenantScopedRepository


class ComunicacionRepository(TenantScopedRepository[Comunicacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str) -> None:
        super().__init__(session, Comunicacion, tenant_id)

    async def crear(self, **kwargs) -> Comunicacion:
        return await self.create(**kwargs)

    async def get(self, comunicacion_id: UUID) -> Comunicacion | None:
        return await self.get_by_id(comunicacion_id)

    async def listar_por_lote(self, lote_id: UUID) -> list[Comunicacion]:
        result = await self.session.execute(
            self._statement().where(Comunicacion.lote_id == lote_id)
        )
        return list(result.scalars().all())

    async def listar_por_estado_pendiente(
        self,
        requiere_aprobacion: bool = False,
        limit: int = 50,
    ) -> list[Comunicacion]:
        stmt = self._statement().where(
            Comunicacion.estado == EstadoComunicacion.PENDIENTE
        )
        if requiere_aprobacion:
            stmt = stmt.where(Comunicacion.aprobado_por.isnot(None))
        stmt = stmt.limit(limit).order_by(Comunicacion.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def listar_huerfanos_global(
        self, timeout: timedelta
    ) -> list[Comunicacion]:
        """Find ENVIANDO messages older than timeout (across all tenants)."""
        cutoff = datetime.now(timezone.utc) - timeout
        result = await self.session.execute(
            select(Comunicacion)
            .where(Comunicacion.estado == EstadoComunicacion.ENVIANDO)
            .where(Comunicacion.updated_at < cutoff)
            .where(Comunicacion.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def aprobar_lote(
        self, lote_id: UUID, aprobado_por: UUID
    ) -> int:
        mensajes = await self.listar_por_lote(lote_id)
        pendientes = [
            m for m in mensajes if m.estado == EstadoComunicacion.PENDIENTE
        ]
        for m in pendientes:
            m.aprobado_por = aprobado_por
        await self.session.flush()
        return len(pendientes)

    async def rechazar_lote(self, lote_id: UUID) -> int:
        mensajes = await self.listar_por_lote(lote_id)
        pendientes = [
            m for m in mensajes if m.estado == EstadoComunicacion.PENDIENTE
        ]
        for m in pendientes:
            m.cancelar()
        await self.session.flush()
        return len(pendientes)

    async def aprobar_individual(
        self, comunicacion_id: UUID, aprobado_por: UUID
    ) -> Comunicacion | None:
        m = await self.get(comunicacion_id)
        if m is None or m.estado != EstadoComunicacion.PENDIENTE:
            return None
        m.aprobado_por = aprobado_por
        await self.session.flush()
        return m

    async def rechazar_individual(
        self, comunicacion_id: UUID
    ) -> Comunicacion | None:
        m = await self.get(comunicacion_id)
        if m is None or m.estado != EstadoComunicacion.PENDIENTE:
            return None
        m.cancelar()
        await self.session.flush()
        return m
