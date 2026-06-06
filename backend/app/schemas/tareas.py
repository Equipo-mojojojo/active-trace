from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, BaseModel

from app.models.enums import EstadoTarea


class TareaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asignado_a: UUID
    descripcion: str
    materia_id: UUID | None = None
    contexto_id: UUID | None = None


class TareaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estado: EstadoTarea | None = None
    descripcion: str | None = None


class TareaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    materia_id: UUID | None = None
    asignado_a: UUID
    asignado_por: UUID
    estado: EstadoTarea
    descripcion: str
    contexto_id: UUID | None = None


class ComentarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str


class ComentarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    tarea_id: UUID
    autor_id: UUID
    texto: str
    creado_at: datetime
