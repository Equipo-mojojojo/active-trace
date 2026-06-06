"""
Schemas Pydantic para Análisis y Reportes (C-11).

Todos los schemas usan extra='forbid'.
DTOs para:
- Alumnos atrasados (F2.2, RN-06)
- Ranking de actividades aprobadas (F2.3, RN-09)
- Reporte rápido por materia (F2.4)
- Notas finales agrupadas (F2.5)
- Monitor de seguimiento (F2.7–F2.9)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Filtros (query params)
# ---------------------------------------------------------------------------


class AtrasadosFiltros(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comision: Optional[str] = None


class FiltrosMonitor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[UUID] = None
    comision: Optional[str] = None
    regional: Optional[str] = None
    q: Optional[str] = None
    min_aprobadas: Optional[int] = Field(default=None, ge=0)
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    limit: int = Field(default=1000, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Atrasados (F2.2)
# ---------------------------------------------------------------------------


class AlumnoAtrasado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    comision: Optional[str] = None
    materia_id: UUID
    actividades_faltantes: list[str]
    actividades_reprobadas: list[str]


class AtrasadosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    atrasados: list[AlumnoAtrasado]


# ---------------------------------------------------------------------------
# Ranking (F2.3, RN-09)
# ---------------------------------------------------------------------------


class RankingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    comision: Optional[str] = None
    aprobadas: int


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    ranking: list[RankingEntry]


# ---------------------------------------------------------------------------
# Reporte rápido (F2.4)
# ---------------------------------------------------------------------------


class ActividadMetrica(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actividad: str
    total: int
    aprobadas: int
    tasa_aprobacion: float  # 0.0 – 1.0


class ReporteRapidoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    total_alumnos: int
    con_aprobadas: int
    atrasados: int
    actividades: list[ActividadMetrica]


# ---------------------------------------------------------------------------
# Notas finales (F2.5)
# ---------------------------------------------------------------------------


class NotaFinalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    nota_final: Decimal


class NotasFinalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actividades_seleccionadas: list[str]
    notas: list[NotaFinalEntry]


# ---------------------------------------------------------------------------
# Monitor (F2.7–F2.9)
# ---------------------------------------------------------------------------


class MonitorEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    comision: Optional[str] = None
    regional: Optional[str] = None
    materia_id: UUID
    aprobadas: int
    reprobadas: int
    faltantes: int
    atrasado: bool


class MonitorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    entries: list[MonitorEntry]
