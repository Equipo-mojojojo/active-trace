from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoActivo


class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: EstadoActivo | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    estado: EstadoActivo
    created_at: datetime
    updated_at: datetime
