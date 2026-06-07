from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, BaseModel


class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alumno_id: UUID
    nota_final: str | None = None


class ResultadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    nota_final: str | None = None
