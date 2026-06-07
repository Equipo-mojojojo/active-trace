from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComunicacionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    entrada_padron_ids: list[UUID] = Field(min_length=1)
    asunto_template: str = Field(min_length=1, max_length=255)
    cuerpo_template: str = Field(min_length=1)


class ComunicacionPreviewItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    destinatario_nombre: str
    destinatario_email: str
    asunto: str
    cuerpo: str


class ComunicacionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requiere_aprobacion: bool
    preview: list[ComunicacionPreviewItemResponse]


class ComunicacionEnqueueRequest(ComunicacionPreviewRequest):
    model_config = ConfigDict(extra="forbid")


class ComunicacionEstadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    lote_id: UUID
    entrada_padron_id: UUID
    destinatario_nombre: str
    estado: str
    requiere_aprobacion: bool
    aprobada: bool
    error_detalle: str | None = None


class ComunicacionLoteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    total: int
    requiere_aprobacion: bool
    comunicaciones: list[ComunicacionEstadoResponse]


class ComunicacionActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    affected: int
