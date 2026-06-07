from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProgramaMateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str


class ProgramaMateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    titulo: str | None = None
    referencia_archivo: str | None = None


class ProgramaMateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime
    created_at: datetime
    updated_at: datetime
