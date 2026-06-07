from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GuardiaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str
    horario: str
    comentarios: str | None = None


class GuardiaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    comentarios: str | None = None


class GuardiaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None = None
    created_at: datetime
    updated_at: datetime
