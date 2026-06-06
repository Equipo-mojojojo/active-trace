from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.repositories.base import TenantScopedRepository


class LiquidacionRepository(TenantScopedRepository[Liquidacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Liquidacion, tenant_id)

    async def list_by_periodo(self, periodo: str) -> list[Liquidacion]:
        result = await self.session.execute(
            self._statement()
            .where(Liquidacion.periodo == periodo)
            .order_by(Liquidacion.created_at)
        )
        return list(result.scalars().all())

    async def list_cerradas(self) -> list[Liquidacion]:
        result = await self.session.execute(
            self._statement()
            .where(Liquidacion.estado == EstadoLiquidacion.CERRADA)
            .order_by(Liquidacion.periodo.desc())
        )
        return list(result.scalars().all())

    async def cerrar_periodo(self, periodo: str) -> list[Liquidacion]:
        liquidaciones = await self.list_by_periodo(periodo)
        if not liquidaciones:
            raise ValueError("periodo_sin_liquidaciones")
        for liq in liquidaciones:
            if liq.cerrada:
                raise ValueError("liquidacion_cerrada")
        for liq in liquidaciones:
            liq.cerrar()
        await self.session.flush()
        return liquidaciones

    async def update(self, record_id: UUID, **values) -> Liquidacion | None:
        row = await self.get_by_id(record_id)
        if row is None:
            return None
        if row.cerrada:
            raise ValueError("liquidacion_cerrada")
        for k, v in values.items():
            setattr(row, k, v)
        await self.session.flush()
        await self.session.refresh(row)
        return row
