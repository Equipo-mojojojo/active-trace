from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None


class SalarioBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None


class SalarioBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime
