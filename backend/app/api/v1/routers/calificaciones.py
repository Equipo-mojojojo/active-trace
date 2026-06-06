"""
Calificaciones router for C-10: LMS grade import, threshold config, finalization report.

Endpoints:
  POST   /api/v1/calificaciones/preview              — Detect activities (no DB write)
  POST   /api/v1/calificaciones/import               — Import selected activities
  PUT    /api/v1/calificaciones/umbral               — Configure threshold per assignment
  POST   /api/v1/calificaciones/finalizacion/preview — Cross-reference completion report

Architecture:
  - Identity always from JWT (get_current_user), never from request params.
  - Business logic in CalificacionesService, not here.
  - Queries in repositories, not in services or routers.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.calificaciones import (
    FinalizacionPreviewResponse,
    ImportCalificacionesResponse,
    PreviewCalificacionesResponse,
    UmbralMateriaRequest,
    UmbralMateriaResponse,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.calificaciones_parser import CalificacionesParseError
from app.services.calificaciones_service import (
    CalificacionesConflictError,
    CalificacionesForbiddenError,
    CalificacionesNotFoundError,
    CalificacionesService,
)

router = APIRouter(prefix="/api/v1/calificaciones", tags=["calificaciones"])


def _build_service(
    user: User, db: AsyncSession, request: Request
) -> CalificacionesService:
    ctx = get_request_context(request)
    audit = AuditService(db=db, tenant_id=user.tenant_id, **ctx)
    return CalificacionesService(session=db, tenant_id=user.tenant_id, audit=audit)


# ---------------------------------------------------------------------------
# POST /preview — parse file, return detected activities (no DB write)
# ---------------------------------------------------------------------------


@router.post(
    "/preview",
    response_model=PreviewCalificacionesResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_calificaciones(
    materia_id: UUID = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(require_permission("calificaciones:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """Parse the LMS file and return detected activities without persisting."""
    svc = _build_service(user, db, request)
    file_bytes = await file.read()
    try:
        result = await svc.preview_importacion(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            materia_id=materia_id,
        )
    except CalificacionesParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return result


# ---------------------------------------------------------------------------
# POST /import — import selected activities, persist with aprobado derived
# ---------------------------------------------------------------------------


@router.post(
    "/import",
    response_model=ImportCalificacionesResponse,
    status_code=status.HTTP_200_OK,
)
async def importar_calificaciones(
    materia_id: UUID = Form(...),
    actividades_seleccionadas: list[str] = Form(...),
    asignacion_id: UUID | None = Form(default=None),
    file: UploadFile = File(...),
    _: None = Depends(require_permission("calificaciones:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """Import selected grade columns from an LMS file."""
    svc = _build_service(user, db, request)
    file_bytes = await file.read()
    try:
        result = await svc.importar(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            materia_id=materia_id,
            actividades_seleccionadas=actividades_seleccionadas,
            actor=user,
            asignacion_id=asignacion_id,
        )
    except CalificacionesParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except CalificacionesConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CalificacionesNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result


# ---------------------------------------------------------------------------
# PUT /umbral — configure approval threshold per assignment
# ---------------------------------------------------------------------------


@router.put(
    "/umbral",
    response_model=UmbralMateriaResponse,
    status_code=status.HTTP_200_OK,
)
async def configurar_umbral(
    body: UmbralMateriaRequest,
    _: None = Depends(require_permission("calificaciones:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """Create or update UmbralMateria for an assignment."""
    svc = _build_service(user, db, request)
    try:
        result = await svc.configurar_umbral(
            asignacion_id=body.asignacion_id,
            materia_id=body.materia_id,
            umbral_pct=body.umbral_pct,
            valores_aprobatorios=body.valores_aprobatorios,
            actor=user,
        )
    except CalificacionesNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CalificacionesForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return result


# ---------------------------------------------------------------------------
# POST /finalizacion/preview — cross-reference completion report (no DB write)
# ---------------------------------------------------------------------------


@router.post(
    "/finalizacion/preview",
    response_model=FinalizacionPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_finalizacion(
    materia_id: UUID = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(require_permission("calificaciones:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """Parse an LMS completion report and return ungraded textual activities."""
    svc = _build_service(user, db, request)
    file_bytes = await file.read()
    try:
        result = await svc.preview_finalizacion(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            materia_id=materia_id,
        )
    except CalificacionesParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except CalificacionesConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CalificacionesNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result
