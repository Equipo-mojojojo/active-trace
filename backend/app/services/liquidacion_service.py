from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.repositories.salario_base_repository import SalarioBaseRepository
from app.repositories.salario_plus_repository import SalarioPlusRepository
from app.services.audit_service import AuditService


class LiquidacionConflictError(RuntimeError):
    pass


class LiquidacionNotFoundError(LookupError):
    pass


def calcular_total(
    salario_base: Decimal,
    comisiones: list[Any],
    plus_lookup: dict[tuple[str, str], Decimal],
    rol: str,
    tenant: Any,
) -> tuple[Decimal, Decimal]:
    """Pure function: returns (monto_base, monto_plus)."""
    comisiones_con_plus = [c for c in comisiones if c.materia.grupo_plus_clave]

    if tenant.tope_plus is not None:
        comisiones_con_plus = comisiones_con_plus[: tenant.tope_plus]

    monto_plus = Decimal("0")
    for comision in comisiones_con_plus:
        key = (comision.materia.grupo_plus_clave, rol)
        monto_plus += plus_lookup.get(key, Decimal("0"))

    return salario_base, monto_plus


def segmentar_liquidaciones(liquidaciones: list[Any]) -> Any:
    """Pure function: segments liquidaciones into general/nexo/facturantes + KPIs."""
    general = [l for l in liquidaciones if not l.es_nexo and not l.excluido_por_factura]
    nexo = [l for l in liquidaciones if l.es_nexo]
    facturantes = [l for l in liquidaciones if l.excluido_por_factura]

    total_sin_factura = sum((l.total for l in general + nexo), Decimal("0"))
    total_con_factura = sum((l.total for l in liquidaciones), Decimal("0"))

    return SimpleNamespace(
        general=general,
        nexo=nexo,
        facturantes=facturantes,
        total_sin_factura=total_sin_factura,
        total_con_factura=total_con_factura,
    )


class LiquidacionService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | str,
        audit: AuditService | None = None,
    ):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self.audit = audit
        self._repo = LiquidacionRepository(session, tenant_id)
        self._base_repo = SalarioBaseRepository(session, tenant_id)
        self._plus_repo = SalarioPlusRepository(session, tenant_id)

    async def obtener_segmentada(self, periodo: str) -> Any:
        liquidaciones = await self._repo.list_by_periodo(periodo)
        return segmentar_liquidaciones(liquidaciones)

    async def cerrar_periodo(
        self, periodo: str, actor_id: UUID, actor_tenant_id: UUID
    ) -> list[Liquidacion]:
        try:
            liquidaciones = await self._repo.cerrar_periodo(periodo)
        except ValueError as exc:
            raise LiquidacionConflictError(str(exc)) from exc

        if self.audit:
            await self.audit.log(
                action=AuditAction.LIQUIDACION_CERRAR,
                actor_id=actor_id,
                tenant_id=actor_tenant_id,
                detail={"periodo": periodo, "cerradas": len(liquidaciones)},
            )

        return liquidaciones

    async def historial(self) -> list[Liquidacion]:
        return await self._repo.list_cerradas()
