from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoActivo


class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None
    estado: EstadoActivo = EstadoActivo.ACTIVA


class CohorteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    anio: int | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: EstadoActivo | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None
    estado: EstadoActivo
    created_at: datetime
    updated_at: datetime
