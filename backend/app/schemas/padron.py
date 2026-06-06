"""
Pydantic v2 schemas for the Padron module (C-09).

All schemas use ConfigDict(extra='forbid') per hard project rules.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportarPadronRequest(BaseModel):
    """Form fields for POST /api/padron/importar.

    The file itself arrives as UploadFile (FastAPI form/multipart).
    """

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID


class EntradaPadronPreview(BaseModel):
    """Single student row in a preview response (no plaintext email)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    email_enmascarado: str | None = None
    comision: str | None = None
    regional: str | None = None


class PreviewResponse(BaseModel):
    """Response for POST /api/padron/preview."""

    model_config = ConfigDict(extra="forbid")

    alumnos: list[EntradaPadronPreview]
    columnas_detectadas: list[str]
    total: int


class VersionPadronResponse(BaseModel):
    """Single version entry in GET /api/padron/versiones."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    activa: bool
    total_entradas: int
    origen: str
    created_at: datetime

    @classmethod
    def from_orm(cls, version) -> "VersionPadronResponse":
        return cls(
            id=version.id,
            materia_id=version.materia_id,
            cohorte_id=version.cohorte_id,
            activa=version.activa,
            total_entradas=version.total_entradas,
            origen=version.origen,
            created_at=version.created_at,
        )


class ImportarPadronResponse(BaseModel):
    """Response for POST /api/padron/importar."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    total_entradas: int
    activa: bool
    origen: str


class VaciarPadronResponse(BaseModel):
    """Response for DELETE /api/padron/vaciar."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    activa: bool
    mensaje: str


class SyncMoodleRequest(BaseModel):
    """Request body for POST /api/padron/sync-moodle."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    moodle_course_id: str


class SyncMoodleResponse(BaseModel):
    """Response for POST /api/padron/sync-moodle."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    total_entradas: int
    activa: bool
    origen: str
