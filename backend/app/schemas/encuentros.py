from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SlotEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    titulo: str
    hora: time
    dia_semana: str
    fecha_inicio: date
    cant_semanas: int = 0
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date | None = None


class SlotEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = None
    hora: time | None = None
    dia_semana: str | None = None
    meet_url: str | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None


class SlotEncuentroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asignacion_id: UUID
    materia_id: UUID
    titulo: str
    hora: time
    dia_semana: str
    fecha_inicio: date
    cant_semanas: int
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date | None = None
    created_at: datetime
    updated_at: datetime


class InstanciaEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    slot_id: UUID | None = None
    fecha: date
    hora: time
    titulo: str
    meet_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slot_id: UUID | None = None
    materia_id: UUID
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    created_at: datetime
    updated_at: datetime


class EncuentroExportLMS(BaseModel):
    materia_nombre: str
    html: str
