"""
Pydantic schemas for Asignacion: request/response DTOs.

All schemas use extra='forbid' to reject unknown fields.
Response schemas include computed estado_vigencia.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AsignacionCreateRequest(BaseModel):
    """Request schema for creating an Asignacion."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    rol: str = Field(..., min_length=1, max_length=50)
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[str] = Field(None, max_length=500)
    desde: date
    hasta: Optional[date] = None
    responsable_id: Optional[UUID] = None


class AsignacionUpdateRequest(BaseModel):
    """Request schema for updating an Asignacion (PATCH)."""

    model_config = ConfigDict(extra="forbid")

    responsable_id: Optional[UUID] = None
    hasta: Optional[date] = None
    # Note: usuario_id, rol, desde are NOT updatable


class AsignacionResponseDTO(BaseModel):
    """Response schema for Asignacion (HTTP responses)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    rol: str
    materia_id: Optional[UUID] = None
    carrera_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    comisiones: Optional[str] = None
    desde: date
    hasta: Optional[date] = None
    responsable_id: Optional[UUID] = None
    estado_vigencia: str  # Computed: Vigente, Futura, Vencida
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to compute estado_vigencia."""
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            usuario_id=obj.usuario_id,
            rol=obj.rol if isinstance(obj.rol, str) else obj.rol.value,
            materia_id=obj.materia_id,
            carrera_id=obj.carrera_id,
            cohorte_id=obj.cohorte_id,
            comisiones=obj.comisiones,
            desde=obj.desde,
            hasta=obj.hasta,
            responsable_id=obj.responsable_id,
            estado_vigencia=obj.estado_vigencia,  # This calls the @property
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
