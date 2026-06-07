"""
Pydantic schemas for Usuario: request/response DTOs.

All schemas use extra='forbid' to reject unknown fields.
Response schemas omit PII to prevent accidental exposure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UsuarioCreateRequest(BaseModel):
    """Request schema for creating a Usuario."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=255)
    apellidos: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    dni: Optional[str] = Field(None, min_length=8, max_length=8)
    cuil: Optional[str] = Field(None, pattern=r"^\d{11}$")
    cbu: Optional[str] = Field(None, min_length=22, max_length=22)
    alias_cbu: Optional[str] = Field(None, max_length=50)
    legajo: Optional[str] = Field(None, max_length=50)


class UsuarioUpdateRequest(BaseModel):
    """Request schema for updating a Usuario (PATCH)."""

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=255)
    # Note: email and PII fields are NOT updatable


class UsuarioResponseDTO(BaseModel):
    """Response schema for Usuario (HTTP responses)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    legajo: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: datetime

    # PII fields are intentionally omitted
    # email, dni, cuil, cbu, alias_cbu must NEVER be in HTTP responses

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to ensure PII is never serialized."""
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            nombre=obj.nombre,
            apellidos=obj.apellidos,
            legajo=obj.legajo,
            estado=obj.estado.value if hasattr(obj.estado, "value") else str(obj.estado),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
