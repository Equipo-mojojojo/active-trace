"""
Schemas Pydantic para Calificaciones (C-10).

Todos los schemas usan extra='forbid' para rechazar campos desconocidos.
DTOs para:
- Preview de importación de calificaciones LMS
- Importación de calificaciones (con actividades seleccionadas)
- Configuración de UmbralMateria
- Preview de reporte de finalización
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActividadDetectadaSchema(BaseModel):
    """One detected grade column from an LMS file."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    tipo: str  # "numerica" | "textual"
    muestra_valores: list[str] = Field(default_factory=list)


class PreviewCalificacionesResponse(BaseModel):
    """Response from POST /calificaciones/preview."""

    model_config = ConfigDict(extra="forbid")

    actividades: list[ActividadDetectadaSchema]


class ImportCalificacionesResponse(BaseModel):
    """Response from POST /calificaciones/import."""

    model_config = ConfigDict(extra="forbid")

    importadas: int


class UmbralMateriaRequest(BaseModel):
    """Request body for PUT /calificaciones/umbral."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    umbral_pct: int = Field(default=60, ge=0, le=100)
    valores_aprobatorios: list[str] = Field(default_factory=list)


class UmbralMateriaResponse(BaseModel):
    """Response from PUT /calificaciones/umbral."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    asignacion_id: UUID
    umbral_pct: int
    valores_aprobatorios: list[str]


class EntradaPendienteCorreccionSchema(BaseModel):
    """One pending-correction entry from the finalization report."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    actividad: str


class FinalizacionPreviewResponse(BaseModel):
    """Response from POST /calificaciones/finalizacion/preview."""

    model_config = ConfigDict(extra="forbid")

    pendientes: list[EntradaPendienteCorreccionSchema]
