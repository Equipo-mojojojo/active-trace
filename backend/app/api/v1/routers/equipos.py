"""
Equipos router for C-08: Domain-level team management endpoints.

Endpoints:
- GET  /api/equipos/mis-equipos       — Own assignments (any authenticated user)
- GET  /api/equipos/asignaciones      — All tenant assignments (equipos:asignar)
- POST /api/equipos/asignaciones/masiva — Bulk assignment (equipos:asignar)
- POST /api/equipos/clonar            — Clone team between cohortes (equipos:asignar)
- PATCH /api/equipos/vigencia         — Bulk vigency update (equipos:asignar)
- GET  /api/equipos/export            — CSV export (equipos:asignar)

Architecture rules:
- Identity always from JWT (get_current_user), never from request params.
- Business logic always in EquiposService, never in this router.
- Queries always in EquiposRepository, never in services or routers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionResponse,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    MisEquiposFiltros,
    ModificarVigenciaRequest,
    ModificarVigenciaResponse,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.equipos_service import (
    EquiposConflictError,
    EquiposNotFoundError,
    EquiposService,
)

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


def _build_service(
    user: User,
    db: AsyncSession,
    request: Request,
) -> EquiposService:
    """Build EquiposService with AuditService wired."""
    ctx = get_request_context(request)
    audit = AuditService(db=db, tenant_id=user.tenant_id, **ctx)
    return EquiposService(session=db, tenant_id=user.tenant_id, audit=audit)


# ---------------------------------------------------------------------------
# GET /mis-equipos — no extra permission guard (own identity from JWT)
# ---------------------------------------------------------------------------


@router.get("/mis-equipos", response_model=list[AsignacionResponse])
async def get_mis_equipos(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    estado: str | None = Query(None, description="Vigente | Vencida | Futura"),
    materia_id: str | None = None,
    rol: str | None = None,
    carrera_id: str | None = None,
    cohorte_id: str | None = None,
) -> list[AsignacionResponse]:
    """
    Return all assignments for the authenticated user.

    No additional permission guard — scope is limited to the actor's own
    assignments by identity (JWT). All users can call this endpoint.
    """
    from uuid import UUID

    filtros = MisEquiposFiltros(
        estado=estado,
        materia_id=UUID(materia_id) if materia_id else None,
        rol=rol,
        carrera_id=UUID(carrera_id) if carrera_id else None,
        cohorte_id=UUID(cohorte_id) if cohorte_id else None,
    )
    service = _build_service(user, db, request)
    return await service.mis_equipos(actor_id=user.id, filtros=filtros)


# ---------------------------------------------------------------------------
# GET /asignaciones — requires equipos:asignar
# ---------------------------------------------------------------------------


@router.get("/asignaciones", response_model=list[AsignacionResponse])
async def get_asignaciones(
    request: Request,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    estado: str | None = Query(None),
    materia_id: str | None = None,
    rol: str | None = None,
    carrera_id: str | None = None,
    cohorte_id: str | None = None,
    usuario_id: str | None = None,
) -> list[AsignacionResponse]:
    """
    Return all assignments in the tenant (COORDINADOR/ADMIN view).

    Requires `equipos:asignar` permission.
    """
    from uuid import UUID

    filtros = MisEquiposFiltros(
        estado=estado,
        materia_id=UUID(materia_id) if materia_id else None,
        rol=rol,
        carrera_id=UUID(carrera_id) if carrera_id else None,
        cohorte_id=UUID(cohorte_id) if cohorte_id else None,
    )
    service = _build_service(user, db, request)
    return await service.consultar_asignaciones(filtros=filtros)


# ---------------------------------------------------------------------------
# POST /asignaciones/masiva — requires equipos:asignar
# ---------------------------------------------------------------------------


@router.post(
    "/asignaciones/masiva",
    response_model=AsignacionMasivaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_asignacion_masiva(
    payload: AsignacionMasivaRequest,
    request: Request,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionMasivaResponse:
    """
    Create N assignments in a single atomic transaction (RN-30).

    Returns 201 on success, 409 if any assignment conflicts.
    Requires `equipos:asignar` permission.
    """
    service = _build_service(user, db, request)
    try:
        return await service.asignacion_masiva(actor_id=user.id, payload=payload)
    except EquiposConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "conflictos": exc.conflictos},
        ) from exc


# ---------------------------------------------------------------------------
# POST /clonar — requires equipos:asignar
# ---------------------------------------------------------------------------


@router.post("/clonar", response_model=ClonarEquipoResponse)
async def post_clonar_equipo(
    payload: ClonarEquipoRequest,
    request: Request,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClonarEquipoResponse:
    """
    Clone vigent assignments from an origin team to a destination cohorte (RN-12).

    Returns clonadas=0 with a message if no vigent assignments exist (not an error).
    Requires `equipos:asignar` permission.
    """
    service = _build_service(user, db, request)
    return await service.clonar_equipo(actor_id=user.id, payload=payload)


# ---------------------------------------------------------------------------
# PATCH /vigencia — requires equipos:asignar
# ---------------------------------------------------------------------------


@router.patch("/vigencia", response_model=ModificarVigenciaResponse)
async def patch_vigencia(
    payload: ModificarVigenciaRequest,
    request: Request,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModificarVigenciaResponse:
    """
    Bulk update desde/hasta for a team's assignments.

    Supports dry_run=true to preview the count before executing.
    Requires `equipos:asignar` permission.
    """
    service = _build_service(user, db, request)
    try:
        return await service.modificar_vigencia(actor_id=user.id, payload=payload)
    except EquiposNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /export — requires equipos:asignar
# ---------------------------------------------------------------------------


@router.get("/export")
async def get_export_csv(
    request: Request,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    materia_id: str | None = None,
    carrera_id: str | None = None,
    cohorte_id: str | None = None,
    estado: str | None = None,
) -> StreamingResponse:
    """
    Export team assignments as a downloadable CSV file.

    Design D4: CSV generated in memory with stdlib csv.DictWriter.
    Returns text/csv with Content-Disposition: attachment.
    Requires `equipos:asignar` permission.
    """
    from uuid import UUID

    filtros = MisEquiposFiltros(
        estado=estado,
        materia_id=UUID(materia_id) if materia_id else None,
        carrera_id=UUID(carrera_id) if carrera_id else None,
        cohorte_id=UUID(cohorte_id) if cohorte_id else None,
    )
    service = _build_service(user, db, request)
    csv_content = await service.exportar_csv(filtros=filtros)

    filename = "equipo"
    if materia_id:
        filename += f"_{materia_id[:8]}"
    if cohorte_id:
        filename += f"_{cohorte_id[:8]}"
    filename += ".csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
