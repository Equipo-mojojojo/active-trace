"""Pydantic schemas for the audit log API.

All schemas use ``extra='forbid'`` to reject unexpected fields.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntryResponse(BaseModel):
    """A single audit log entry returned by the API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    actor_id: UUID
    impersonado_id: UUID | None = None
    materia_id: UUID | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int | None = None
    ip: str | None = None
    user_agent: str | None = None
    fecha_hora: datetime


class AuditLogListResponse(BaseModel):
    """Paginated audit log list."""

    model_config = ConfigDict(extra="forbid")

    entries: list[AuditLogEntryResponse]
    total: int
    page: int
    page_size: int


# ── Impersonation schemas ────────────────────────────────────────────


class IniciarImpersonacionRequest(BaseModel):
    """Request body to start impersonation."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID


class ImpersonacionTokenResponse(BaseModel):
    """Response containing the impersonation (or normal) access token."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
