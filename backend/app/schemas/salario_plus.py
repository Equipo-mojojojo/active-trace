from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None = None


class SalarioPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descripcion: str | None = None
    monto: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None


class SalarioPlusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime
