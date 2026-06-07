from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import EstadoFactura, Factura
from app.repositories.base import TenantScopedRepository


class FacturaRepository(TenantScopedRepository[Factura]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Factura, tenant_id)

    async def list_by_tenant(
        self,
        estado: str | None = None,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
    ) -> list[Factura]:
        stmt = self._statement().order_by(Factura.fecha_carga.desc())
        if estado:
            stmt = stmt.where(Factura.estado == estado)
        if periodo:
            stmt = stmt.where(Factura.periodo == periodo)
        if usuario_id:
            stmt = stmt.where(Factura.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_estado(self, record_id: UUID, estado: str) -> Factura | None:
        row = await self.get_by_id(record_id)
        if row is None:
            return None
        row.estado = estado
        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def update_archivo_path(self, record_id: UUID, archivo_path: str) -> Factura | None:
        row = await self.get_by_id(record_id)
        if row is None:
            return None
        row.archivo_path = archivo_path
        await self.session.flush()
        await self.session.refresh(row)
        return row
