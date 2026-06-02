"""Audit log query API — ``GET /api/admin/audit-log``.

All endpoints are protected by ``require_permission("auditoria:ver")``
and support ``:propio`` scoping for users who can only see their own
actions.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import get_effective_permissions, require_permission
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogEntryResponse, AuditLogListResponse

router = APIRouter(prefix="/api/admin", tags=["admin-audit"])


@router.get("/audit-log", response_model=AuditLogListResponse)
async def list_audit_log(
    desde: date | None = Query(None, description="Filter: start date (inclusive)"),
    hasta: date | None = Query(None, description="Filter: end date (inclusive)"),
    actor_id: UUID | None = Query(None, description="Filter by actor user ID"),
    materia_id: UUID | None = Query(None, description="Filter by subject instance ID"),
    accion: str | None = Query(None, description="Filter by action code"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    _: None = Depends(require_permission("auditoria:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """List audit log entries for the current tenant.

    Users with the global ``auditoria:ver`` permission see all entries.
    Users with only ``auditoria:ver:propio`` see only entries where
    they are the actor.
    """
    # ── Resolve :propio scoping ────────────────────────────────────
    # require_permission("auditoria:ver") already passed, so the user
    # has either "auditoria:ver" (global) or "auditoria:ver:propio".
    # We check which one to decide the effective actor filter.
    effective_perms = await get_effective_permissions(
        user_id=user.id,
        tenant_id=user.tenant_id,
        db=db,
    )

    has_global = "auditoria:ver" in effective_perms
    # If they don't have global, they must have :propio (guard passed)
    effective_actor_id = actor_id
    if not has_global:
        effective_actor_id = user.id

    # ── Convert dates to datetimes ─────────────────────────────────
    desde_dt = datetime.combine(desde, datetime.min.time()) if desde else None
    hasta_dt = datetime.combine(hasta, datetime.max.time()) if hasta else None

    # ── Query ──────────────────────────────────────────────────────
    repository = AuditLogRepository(db, tenant_id=user.tenant_id)
    entries, total = await repository.list_entries(
        desde=desde_dt,
        hasta=hasta_dt,
        actor_id=effective_actor_id,
        materia_id=materia_id,
        accion=accion,
        page=page,
        page_size=page_size,
    )

    return AuditLogListResponse(
        entries=[AuditLogEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )
