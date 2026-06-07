from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    descripcion: str | None = None


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    descripcion: str | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    descripcion: str | None = None
    editable: bool


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    modulo: str
    accion: str
    descripcion: str | None = None


class PermissionAssign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permiso_id: UUID
