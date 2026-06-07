from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import TenantScopedRepository


class ComunicacionRepository(TenantScopedRepository[Comunicacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Comunicacion, tenant_id)

    async def create_many(self, comunicaciones: list[dict]) -> list[Comunicacion]:
        rows = [
            Comunicacion(tenant_id=self.tenant_id, **payload)
            for payload in comunicaciones
        ]
        self.session.add_all(rows)
        await self.session.flush()
        return rows

    async def list_by_lote(self, lote_id: UUID) -> list[Comunicacion]:
        result = await self.session.execute(
            self._statement()
            .where(Comunicacion.lote_id == lote_id)
            .order_by(Comunicacion.created_at)
        )
        return list(result.scalars().all())

    async def get_active_entries_for_materia(
        self,
        materia_id: UUID,
        entrada_padron_ids: list[UUID],
    ) -> list[EntradaPadron]:
        statement: Select[tuple[EntradaPadron]] = (
            select(EntradaPadron)
            .join(VersionPadron, VersionPadron.id == EntradaPadron.version_id)
            .where(EntradaPadron.tenant_id == self.tenant_id)
            .where(VersionPadron.tenant_id == self.tenant_id)
            .where(EntradaPadron.deleted_at.is_(None))
            .where(VersionPadron.deleted_at.is_(None))
            .where(VersionPadron.activa.is_(True))
            .where(VersionPadron.materia_id == materia_id)
            .where(EntradaPadron.id.in_(entrada_padron_ids))
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_pending_eligible(self, limit: int = 100) -> list[Comunicacion]:
        statement = (
            self._statement()
            .where(Comunicacion.estado == EstadoComunicacion.PENDIENTE)
            .where(
                or_(
                    Comunicacion.requiere_aprobacion.is_(False),
                    Comunicacion.aprobada_at.is_not(None),
                )
            )
            .order_by(Comunicacion.created_at)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
