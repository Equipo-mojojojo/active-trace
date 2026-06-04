"""
Padron router for C-09: Roster import, versioning, and Moodle sync.

Endpoints:
  POST   /api/padron/preview      — Parse file, return preview (no DB write)
  POST   /api/padron/importar     — Import file, create new active version
  DELETE /api/padron/vaciar       — Soft-delete active version (scope-isolated)
  GET    /api/padron/versiones    — List all versions for (materia, cohorte)
  POST   /api/padron/sync-moodle  — Sync from Moodle on-demand

Architecture:
  - Identity always from JWT (get_current_user), never from request params.
  - Business logic in PadronService, not here.
  - Queries in PadronRepository, not in services or routers.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.integrations.moodle_ws import MoodleNotConfiguredError, MoodleWSError
from app.models.user import User
from app.schemas.padron import (
    ImportarPadronResponse,
    PreviewResponse,
    EntradaPadronPreview,
    SyncMoodleRequest,
    SyncMoodleResponse,
    VaciarPadronResponse,
    VersionPadronResponse,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.padron_parser import PadronParseError
from app.services.padron_service import (
    PadronForbiddenError,
    PadronNotFoundError,
    PadronService,
)

router = APIRouter(prefix="/api/padron", tags=["padron"])


def _build_service(
    user: User,
    db: AsyncSession,
    request: Request,
) -> PadronService:
    ctx = get_request_context(request)
    audit = AuditService(db=db, tenant_id=user.tenant_id, **ctx)
    return PadronService(session=db, tenant_id=user.tenant_id, audit=audit)


# ---------------------------------------------------------------------------
# POST /preview — parse file, return preview without persisting
# ---------------------------------------------------------------------------


@router.post("/preview", response_model=PreviewResponse)
async def post_preview(
    request: Request,
    _: None = Depends(require_permission("padron:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> PreviewResponse:
    """Parse a padron file and return detected students without writing to DB.

    Returns 422 if the file format is unsupported or exceeds the row limit.
    """
    file_bytes = await file.read()
    filename = file.filename or "upload.csv"

    service = _build_service(user, db, request)

    try:
        result = await service.preview(file_bytes, filename)
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    alumnos = [
        EntradaPadronPreview(
            nombre=a.get("nombre"),
            apellidos=a.get("apellidos"),
            email_enmascarado=a.get("email_enmascarado"),
            comision=a.get("comision"),
            regional=a.get("regional"),
        )
        for a in result["alumnos"]
    ]

    return PreviewResponse(
        alumnos=alumnos,
        columnas_detectadas=result["columnas_detectadas"],
        total=result["total"],
    )


# ---------------------------------------------------------------------------
# POST /importar — import file, create new active version
# ---------------------------------------------------------------------------


@router.post(
    "/importar",
    response_model=ImportarPadronResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_importar(
    request: Request,
    _: None = Depends(require_permission("padron:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    materia_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
) -> ImportarPadronResponse:
    """Import a padron file and create a new active version.

    Returns 201 on success, 422 on parse errors, 403 if no permission.
    """
    file_bytes = await file.read()
    filename = file.filename or "upload.csv"

    service = _build_service(user, db, request)

    try:
        version = await service.importar(
            actor=user,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            file_bytes=file_bytes,
            filename=filename,
        )
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except PadronForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return ImportarPadronResponse(
        id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        total_entradas=version.total_entradas,
        activa=version.activa,
        origen=version.origen,
    )


# ---------------------------------------------------------------------------
# DELETE /vaciar — soft-delete active version (scope-isolated)
# ---------------------------------------------------------------------------


@router.delete("/vaciar", response_model=VaciarPadronResponse)
async def delete_vaciar(
    request: Request,
    _: None = Depends(require_permission("padron:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    materia_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
) -> VaciarPadronResponse:
    """Soft-delete the active padron version for (materia, cohorte).

    PROFESOR can only vaciar their own assigned materias.
    COORDINADOR/ADMIN can vaciar any version in the tenant.
    Returns 404 if no active version exists, 403 if scope is insufficient.
    """
    service = _build_service(user, db, request)

    try:
        version = await service.vaciar(
            actor=user,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )
    except PadronNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PadronForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return VaciarPadronResponse(
        id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        activa=version.activa,
        mensaje="Padrón vaciado correctamente.",
    )


# ---------------------------------------------------------------------------
# GET /versiones — list all versions for (materia, cohorte)
# ---------------------------------------------------------------------------


@router.get("/versiones", response_model=list[VersionPadronResponse])
async def get_versiones(
    request: Request,
    _: None = Depends(require_permission("padron:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    materia_id: UUID = None,
    cohorte_id: UUID = None,
) -> list[VersionPadronResponse]:
    """Return all versions (active + historical) for a (materia, cohorte) pair."""
    if materia_id is None or cohorte_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="materia_id y cohorte_id son requeridos.",
        )

    service = _build_service(user, db, request)
    versions = await service.listar_versiones(materia_id, cohorte_id)
    return [VersionPadronResponse.from_orm(v) for v in versions]


# ---------------------------------------------------------------------------
# POST /sync-moodle — on-demand Moodle sync
# ---------------------------------------------------------------------------


@router.post(
    "/sync-moodle",
    response_model=SyncMoodleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_sync_moodle(
    payload: SyncMoodleRequest,
    request: Request,
    _: None = Depends(require_permission("padron:importar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncMoodleResponse:
    """Sync enrolled users from Moodle and create a new active padron version.

    Returns 502 if LMS fails, 503 if LMS is not configured.
    """
    service = _build_service(user, db, request)

    try:
        version = await service.sync_moodle(
            actor=user,
            materia_id=payload.materia_id,
            cohorte_id=payload.cohorte_id,
            moodle_course_id=payload.moodle_course_id,
        )
    except MoodleNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "La integración con Moodle no está configurada. "
                "Importá el padrón manualmente desde archivo."
            ),
        ) from exc
    except MoodleWSError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Error al conectar con el LMS. "
                "Reintentá en unos minutos o importá el padrón manualmente."
            ),
        ) from exc

    return SyncMoodleResponse(
        id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        total_entradas=version.total_entradas,
        activa=version.activa,
        origen=version.origen,
    )
