from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HiloOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hilo_id: UUID
    asunto: str
    remitente_id: UUID
    total_mensajes: int
    tiene_no_leidos: bool
    ultimo_mensaje_at: datetime


class MensajeInternoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hilo_id: UUID
    remitente_id: UUID
    destinatario_id: UUID
    asunto: str
    cuerpo: str
    leido_at: datetime | None
    created_at: datetime


class MensajeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destinatario_id: UUID
    asunto: str
    cuerpo: str


class MensajeResponder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuerpo: str
