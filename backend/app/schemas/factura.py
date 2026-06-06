from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.factura import EstadoFactura


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str
    monto: Decimal
    detalle: str | None = None
    fecha_carga: date


class FacturaUpdateEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoFactura


class FacturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    periodo: str
    monto: Decimal
    detalle: str | None
    fecha_carga: date
    archivo_path: str | None
    estado: EstadoFactura
    created_at: datetime
    updated_at: datetime
