from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import ConfigDict, BaseModel

from app.models.enums import EstadoEvaluacion, TipoEvaluacion


class TurnoEvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fecha: date
    hora: time
    max_cupo: int = 1


class TurnoEvaluacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fecha: date | None = None
    hora: time | None = None
    max_cupo: int | None = None


class TurnoEvaluacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    evaluacion_id: UUID
    fecha: date
    hora: time
    max_cupo: int


class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    instancia: str
    dias_disponibles: int = 7
    turnos: list[TurnoEvaluacionCreate]


class EvaluacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: TipoEvaluacion | None = None
    instancia: str | None = None
    dias_disponibles: int | None = None


class EvaluacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    instancia: str
    dias_disponibles: int
    estado: EstadoEvaluacion
    turnos: list[TurnoEvaluacionResponse] = []


class ConvocadoImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alumno_ids: list[UUID]


class ConvocadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
