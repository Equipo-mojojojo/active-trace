from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import EstadoComunicacion


class ComunicacionDestinatarioDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    variables: dict[str, str] = {}


class ComunicacionPreviewRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str
    variables: dict[str, str] = {}


class ComunicacionPreviewResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto_renderizado: str
    cuerpo_renderizado: str
    preview_token: str


class ComunicacionEnviarRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str
    destinatarios: list[ComunicacionDestinatarioDTO]
    materia_id: UUID
    preview_token: str | None = None


class ComunicacionEnviarResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    count: int


class ComunicacionResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    enviado_por: UUID
    materia_id: UUID
    asunto: str
    estado: EstadoComunicacion
    lote_id: UUID | None
    enviado_at: datetime | None
    aprobado_por: UUID | None
    reintento_count: int
    created_at: datetime


class LoteResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    mensajes: list[ComunicacionResponseDTO]
    count: int
