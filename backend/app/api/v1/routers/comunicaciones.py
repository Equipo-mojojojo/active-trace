"""
Comunicaciones router for C-12: outgoing message queue and approval.

Endpoints:
  POST   /api/v1/comunicaciones/preview               — Preview template (comunicacion:enviar)
  POST   /api/v1/comunicaciones/enviar                — Enqueue batch (comunicacion:enviar)
  GET    /api/v1/comunicaciones/lotes/{lote_id}       — Get batch (comunicacion:enviar)
  POST   /api/v1/comunicaciones/lotes/{lote_id}/aprobar  — Approve batch (comunicacion:aprobar)
  POST   /api/v1/comunicaciones/lotes/{lote_id}/rechazar — Reject batch (comunicacion:aprobar)
  POST   /api/v1/comunicaciones/{id}/aprobar          — Approve single (comunicacion:aprobar)
  POST   /api/v1/comunicaciones/{id}/rechazar         — Reject single (comunicacion:aprobar)
  POST   /api/v1/comunicaciones/{id}/cancelar         — Cancel single (comunicacion:enviar)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.comunicacion import (
    ComunicacionEnviarRequestDTO,
    ComunicacionEnviarResponseDTO,
    ComunicacionPreviewRequestDTO,
    ComunicacionPreviewResponseDTO,
    ComunicacionResponseDTO,
    LoteResponseDTO,
)
from app.services.audit_service import get_request_context
from app.services.comunicacion_service import (
    ComunicacionNotFoundError,
    ComunicacionService,
    PreviewExpiredError,
    PreviewRequiredError,
    VariableDesconocidaError,
)

router = APIRouter(prefix="/api/v1/comunicaciones", tags=["comunicaciones"])


def _svc(request: Request, db: AsyncSession) -> ComunicacionService:
    ctx = get_request_context(request)
    return ComunicacionService(db, **ctx)


@router.post(
    "/preview",
    response_model=ComunicacionPreviewResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def preview_comunicacion(
    payload: ComunicacionPreviewRequestDTO,
    request: Request,
    _: None = Depends(require_permission("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    try:
        return svc.preview(payload)
    except VariableDesconocidaError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/enviar",
    response_model=ComunicacionEnviarResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def enviar_comunicaciones(
    payload: ComunicacionEnviarRequestDTO,
    request: Request,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    try:
        return await svc.encolar_lote(payload, tenant_id=user.tenant_id, enviado_por=user.id)
    except PreviewRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PreviewExpiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except VariableDesconocidaError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteResponseDTO,
)
async def get_lote(
    lote_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.comunicacion_repository import ComunicacionRepository

    repo = ComunicacionRepository(db, user.tenant_id)
    mensajes = await repo.listar_por_lote(lote_id)
    return LoteResponseDTO(
        lote_id=lote_id,
        mensajes=[ComunicacionResponseDTO.model_validate(m) for m in mensajes],
        count=len(mensajes),
    )


@router.post(
    "/lotes/{lote_id}/aprobar",
    response_model=LoteResponseDTO,
)
async def aprobar_lote(
    lote_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    return await svc.aprobar_lote(lote_id, actor_id=user.id, tenant_id=user.tenant_id)


@router.post(
    "/lotes/{lote_id}/rechazar",
    response_model=LoteResponseDTO,
)
async def rechazar_lote(
    lote_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    return await svc.rechazar_lote(lote_id, actor_id=user.id, tenant_id=user.tenant_id)


@router.post(
    "/{comunicacion_id}/aprobar",
    response_model=ComunicacionResponseDTO,
)
async def aprobar_individual(
    comunicacion_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    try:
        return await svc.aprobar_individual(
            comunicacion_id, actor_id=user.id, tenant_id=user.tenant_id
        )
    except ComunicacionNotFoundError:
        raise HTTPException(status_code=404, detail="Comunicacion not found")


@router.post(
    "/{comunicacion_id}/rechazar",
    response_model=ComunicacionResponseDTO,
)
async def rechazar_individual(
    comunicacion_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:aprobar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    try:
        return await svc.rechazar_individual(
            comunicacion_id, actor_id=user.id, tenant_id=user.tenant_id
        )
    except ComunicacionNotFoundError:
        raise HTTPException(status_code=404, detail="Comunicacion not found")


@router.post(
    "/{comunicacion_id}/cancelar",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancelar_comunicacion(
    comunicacion_id: UUID,
    request: Request,
    _: None = Depends(require_permission("comunicacion:enviar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(request, db)
    try:
        await svc.cancelar(
            comunicacion_id, actor_id=user.id, tenant_id=user.tenant_id
        )
    except ComunicacionNotFoundError:
        raise HTTPException(status_code=404, detail="Comunicacion not found")
