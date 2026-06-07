from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.comunicacion import (
    ComunicacionActionResponse,
    ComunicacionEnqueueRequest,
    ComunicacionLoteResponse,
    ComunicacionPreviewRequest,
    ComunicacionPreviewResponse,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.comunicacion_service import (
    ComunicacionConflictError,
    ComunicacionForbiddenError,
    ComunicacionNotFoundError,
    ComunicacionService,
)

router = APIRouter(prefix="/api/v1/comunicaciones", tags=["comunicaciones"])


def _build_service(
    user: User, db: AsyncSession, request: Request
) -> ComunicacionService:
    context = get_request_context(request)
    audit = AuditService(db=db, tenant_id=user.tenant_id, **context)
    return ComunicacionService(session=db, tenant_id=user.tenant_id, audit=audit)


def _audit_actor_id(request: Request, user: User) -> UUID:
    actor_id = getattr(request.state, "actor_real_id", user.id)
    return UUID(str(actor_id))


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, ComunicacionForbiddenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if isinstance(exc, ComunicacionNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    if isinstance(exc, ComunicacionConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    raise exc


@router.post("/preview", response_model=ComunicacionPreviewResponse)
async def preview_comunicaciones(
    payload: ComunicacionPreviewRequest,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.preview(
            materia_id=payload.materia_id,
            entrada_padron_ids=payload.entrada_padron_ids,
            asunto_template=payload.asunto_template,
            cuerpo_template=payload.cuerpo_template,
            actor=user,
        )
    except Exception as exc:
        _raise_http(exc)


@router.post(
    "/lotes",
    response_model=ComunicacionLoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enqueue_comunicaciones(
    payload: ComunicacionEnqueueRequest,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.enqueue(
            materia_id=payload.materia_id,
            entrada_padron_ids=payload.entrada_padron_ids,
            asunto_template=payload.asunto_template,
            cuerpo_template=payload.cuerpo_template,
            actor=user,
            audit_actor_id=_audit_actor_id(request, user),
        )
    except Exception as exc:
        _raise_http(exc)


@router.get("/lotes/{lote_id}", response_model=ComunicacionLoteResponse)
async def get_lote_comunicaciones(
    lote_id: UUID,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.get_lote(lote_id, actor=user)
    except Exception as exc:
        _raise_http(exc)


@router.post("/lotes/{lote_id}/aprobar", response_model=ComunicacionActionResponse)
async def approve_lote_comunicaciones(
    lote_id: UUID,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.approve_lote(
            lote_id, _audit_actor_id(request, user), actor=user
        )
    except Exception as exc:
        _raise_http(exc)


@router.post("/lotes/{lote_id}/cancelar", response_model=ComunicacionActionResponse)
async def cancel_lote_comunicaciones(
    lote_id: UUID,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.cancel_lote(
            lote_id, _audit_actor_id(request, user), actor=user
        )
    except Exception as exc:
        _raise_http(exc)


@router.post("/{comunicacion_id}/aprobar", response_model=ComunicacionActionResponse)
async def approve_one_comunicacion(
    comunicacion_id: UUID,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.approve_one(
            comunicacion_id, _audit_actor_id(request, user), actor=user
        )
    except Exception as exc:
        _raise_http(exc)


@router.post("/{comunicacion_id}/cancelar", response_model=ComunicacionActionResponse)
async def cancel_one_comunicacion(
    comunicacion_id: UUID,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    service = _build_service(user, db, request)
    try:
        return await service.cancel_one(
            comunicacion_id, _audit_actor_id(request, user), actor=user
        )
    except Exception as exc:
        _raise_http(exc)
