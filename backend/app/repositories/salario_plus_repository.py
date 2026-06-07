from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_plus import SalarioPlus
from app.repositories.base import TenantScopedRepository
from app.repositories.salario_base_repository import vigencias_solapan


class SalarioPlusRepository(TenantScopedRepository[SalarioPlus]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, SalarioPlus, tenant_id)

    async def _has_overlap(self, grupo: str, rol: str, desde: date, hasta: date | None, exclude_id: UUID | None = None) -> bool:
        result = await self.session.execute(
            self._statement()
            .where(SalarioPlus.grupo == grupo)
            .where(SalarioPlus.rol == rol)
        )
        existing = result.scalars().all()
        for row in existing:
            if exclude_id and row.id == exclude_id:
                continue
            if vigencias_solapan(row.desde, row.hasta, desde, hasta):
                return True
        return False

    async def create_plus(
        self,
        grupo: str,
        rol: str,
        descripcion: str,
        monto: Decimal,
        desde: date,
        hasta: date | None = None,
    ) -> SalarioPlus:
        if await self._has_overlap(grupo, rol, desde, hasta):
            raise ValueError("solapamiento_vigencia")
        return await self.create(
            grupo=grupo, rol=rol, descripcion=descripcion, monto=monto, desde=desde, hasta=hasta
        )

    async def list_by_tenant(self, grupo: str | None = None, rol: str | None = None) -> list[SalarioPlus]:
        stmt = self._statement().order_by(SalarioPlus.grupo, SalarioPlus.rol, SalarioPlus.desde)
        if grupo:
            stmt = stmt.where(SalarioPlus.grupo == grupo)
        if rol:
            stmt = stmt.where(SalarioPlus.rol == rol)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_vigente(self, grupo: str, rol: str, periodo: str) -> SalarioPlus | None:
        periodo_date = date(int(periodo[:4]), int(periodo[5:7]), 1)
        result = await self.session.execute(
            self._statement()
            .where(SalarioPlus.grupo == grupo)
            .where(SalarioPlus.rol == rol)
            .where(SalarioPlus.desde <= periodo_date)
        )
        candidates = result.scalars().all()
        for row in sorted(candidates, key=lambda r: r.desde, reverse=True):
            if row.hasta is None or row.hasta >= periodo_date:
                return row
        return None

    async def update(self, record_id: UUID, **values) -> SalarioPlus | None:
        row = await self.get_by_id(record_id)
        if row is None:
            return None
        if any(k in values for k in ("grupo", "rol", "desde", "hasta")):
            grupo = values.get("grupo", row.grupo)
            rol = values.get("rol", row.rol)
            desde = values.get("desde", row.desde)
            hasta = values.get("hasta", row.hasta)
            if await self._has_overlap(grupo, rol, desde, hasta, exclude_id=record_id):
                raise ValueError("solapamiento_vigencia")
        for k, v in values.items():
            setattr(row, k, v)
        await self.session.flush()
        await self.session.refresh(row)
        return row
