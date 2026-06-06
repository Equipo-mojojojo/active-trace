from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.repositories.base import TenantScopedRepository


def vigencias_solapan(
    existing_desde: date,
    existing_hasta: date | None,
    new_desde: date,
    new_hasta: date | None,
) -> bool:
    """Return True if two date ranges overlap (inclusive bounds)."""
    e_end = existing_hasta or date.max
    n_end = new_hasta or date.max
    return new_desde <= e_end and existing_desde <= n_end


class SalarioBaseRepository(TenantScopedRepository[SalarioBase]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, SalarioBase, tenant_id)

    async def _has_overlap(self, rol: str, desde: date, hasta: date | None, exclude_id: UUID | None = None) -> bool:
        result = await self.session.execute(
            self._statement().where(SalarioBase.rol == rol)
        )
        existing = result.scalars().all()
        for row in existing:
            if exclude_id and row.id == exclude_id:
                continue
            if vigencias_solapan(row.desde, row.hasta, desde, hasta):
                return True
        return False

    async def create_base(self, rol: str, monto: Decimal, desde: date, hasta: date | None = None) -> SalarioBase:
        if await self._has_overlap(rol, desde, hasta):
            raise ValueError("solapamiento_vigencia")
        return await self.create(rol=rol, monto=monto, desde=desde, hasta=hasta)

    async def list_by_tenant(self) -> list[SalarioBase]:
        result = await self.session.execute(
            self._statement().order_by(SalarioBase.rol, SalarioBase.desde)
        )
        return list(result.scalars().all())

    async def get_vigente(self, rol: str, periodo: str) -> SalarioBase | None:
        periodo_date = date(int(periodo[:4]), int(periodo[5:7]), 1)
        result = await self.session.execute(
            self._statement()
            .where(SalarioBase.rol == rol)
            .where(SalarioBase.desde <= periodo_date)
        )
        candidates = result.scalars().all()
        for row in sorted(candidates, key=lambda r: r.desde, reverse=True):
            if row.hasta is None or row.hasta >= periodo_date:
                return row
        return None

    async def update(self, record_id: UUID, **values) -> SalarioBase | None:
        row = await self.get_by_id(record_id)
        if row is None:
            return None
        if "rol" in values or "desde" in values or "hasta" in values:
            rol = values.get("rol", row.rol)
            desde = values.get("desde", row.desde)
            hasta = values.get("hasta", row.hasta)
            if await self._has_overlap(rol, desde, hasta, exclude_id=record_id):
                raise ValueError("solapamiento_vigencia")
        for k, v in values.items():
            setattr(row, k, v)
        await self.session.flush()
        await self.session.refresh(row)
        return row
