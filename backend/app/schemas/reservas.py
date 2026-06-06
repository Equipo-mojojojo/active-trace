from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import ConfigDict, BaseModel

from app.models.enums import EstadoReserva


class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turno_id: UUID


class ReservaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    turno_id: UUID
    alumno_id: UUID
    estado: EstadoReserva


class ReservaDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    turno_id: UUID
    alumno_id: UUID
    estado: EstadoReserva
    fecha: date | None = None
    hora: time | None = None
