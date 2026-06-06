from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.liquidacion import EstadoLiquidacion


class LiquidacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    periodo: str
    usuario_id: UUID
    rol: str
    comisiones: list
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: EstadoLiquidacion
    created_at: datetime
    updated_at: datetime


class LiquidacionSegmentadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    general: list[LiquidacionOut]
    nexo: list[LiquidacionOut]
    facturantes: list[LiquidacionOut]
    total_sin_factura: Decimal
    total_con_factura: Decimal


class CerrarLiquidacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    periodo: str
    liquidaciones_cerradas: int
    estado: str = EstadoLiquidacion.CERRADA
