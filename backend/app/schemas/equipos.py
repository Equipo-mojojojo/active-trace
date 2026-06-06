"""
Schemas Pydantic para Equipos docentes (C-08).

Todos los schemas usan extra='forbid' para rechazar campos desconocidos.
Incluye request/response DTOs para las operaciones de equipos:
- MisEquiposFiltros: filtros para GET /mis-equipos
- AsignacionResponse: respuesta enriquecida con estado_vigencia
- AsignacionMasivaRequest: alta masiva de docentes
- ClonarEquipoRequest: clonado entre períodos
- ModificarVigenciaRequest: modificación de vigencia en bloque
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MisEquiposFiltros(BaseModel):
    """Filtros opcionales para GET /mis-equipos."""

    model_config = ConfigDict(extra="forbid")

    estado: Optional[str] = None          # "Vigente" | "Vencida" | "Futura"
    materia_id: Optional[UUID] = None
    rol: Optional[str] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None


class AsignacionResponse(BaseModel):
    """
    Response DTO para una asignación de equipo docente.

    Incluye estado_vigencia derivado y datos del usuario sin exponer PII cifrada.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    nombre_usuario: Optional[str] = None   # nombre plano, sin PII cifrada
    rol: str
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[str] = None
    desde: date
    hasta: Optional[date] = None
    responsable_id: Optional[UUID] = None
    estado_vigencia: str                   # "Vigente" | "Vencida" | "Futura"
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj, nombre_usuario: Optional[str] = None) -> "AsignacionResponse":
        """Build response DTO from ORM instance."""
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            usuario_id=obj.usuario_id,
            nombre_usuario=nombre_usuario,
            rol=obj.rol if isinstance(obj.rol, str) else obj.rol.value,
            materia_id=obj.materia_id,
            carrera_id=obj.carrera_id,
            cohorte_id=obj.cohorte_id,
            comisiones=obj.comisiones,
            desde=obj.desde,
            hasta=obj.hasta,
            responsable_id=obj.responsable_id,
            estado_vigencia=obj.estado_vigencia,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class AsignacionMasivaRequest(BaseModel):
    """Request para alta masiva de docentes en un equipo."""

    model_config = ConfigDict(extra="forbid")

    usuarios: list[UUID] = Field(..., min_length=1)
    rol: str = Field(..., min_length=1, max_length=50)
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[str] = Field(None, max_length=500)
    responsable_id: Optional[UUID] = None
    desde: date
    hasta: Optional[date] = None


class AsignacionMasivaResponse(BaseModel):
    """Respuesta de alta masiva."""

    model_config = ConfigDict(extra="forbid")

    creadas: int
    asignaciones: list[AsignacionResponse]


class ClonarEquipoRequest(BaseModel):
    """Request para clonar un equipo entre períodos (cohortes)."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id_origen: UUID
    cohorte_id_destino: UUID
    desde: date
    hasta: Optional[date] = None


class ClonarEquipoResponse(BaseModel):
    """Respuesta del clonado de equipo."""

    model_config = ConfigDict(extra="forbid")

    clonadas: int
    mensaje: str
    asignaciones: list[AsignacionResponse]


class ModificarVigenciaRequest(BaseModel):
    """Request para modificar vigencia de un equipo en bloque."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    desde: date
    hasta: Optional[date] = None
    dry_run: bool = False


class ModificarVigenciaResponse(BaseModel):
    """Respuesta de modificación de vigencia."""

    model_config = ConfigDict(extra="forbid")

    afectadas: int
    dry_run: bool
    mensaje: str
