from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AUDIT_MAX_LIMIT = 200


class AccionPorDiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: date
    total: int


class EstadoComunicacionPorDocenteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    materia_id: UUID | None
    estado: str
    total: int


class InteraccionPorDocenteMateriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor_id: UUID
    materia_id: UUID | None
    accion: str
    total: int


class UltimaAccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    actor_id: UUID
    accion: str
    materia_id: UUID | None
    filas_afectadas: int | None
    ip: str | None
    fecha_hora: datetime
