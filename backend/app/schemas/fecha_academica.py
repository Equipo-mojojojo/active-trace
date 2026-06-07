from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoEvaluacion


class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    numero: int
    periodo: str
    fecha: date
    titulo: str


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    tipo: TipoEvaluacion | None = None
    numero: int | None = None
    periodo: str | None = None
    fecha: date | None = None
    titulo: str | None = None


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    numero: int
    periodo: str
    fecha: date
    titulo: str
    created_at: datetime
    updated_at: datetime
