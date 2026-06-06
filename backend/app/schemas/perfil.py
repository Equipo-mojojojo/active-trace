from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

MODALIDADES_VALIDAS = {"liquidacion", "factura"}


class PerfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    legajo: str | None
    legajo_profesional: str | None
    banco: str | None
    cbu: str | None
    alias_cbu: str | None
    regional: str | None
    facturador: bool
    modalidad_cobro: str
    created_at: datetime
    updated_at: datetime


class PerfilUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    banco: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
    modalidad_cobro: str | None = None
