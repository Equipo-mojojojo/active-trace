from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.avisos import (
    AcknowledgmentResponse,
    AvisoCreate,
    AvisoDetailResponse,
    AvisoResponse,
    AvisoUpdate,
)
from app.services.acknowledgment_service import AcknowledgmentService
from app.services.audit_service import AuditService, get_request_context
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/v1/avisos", tags=["avisos"])


def _aviso_service(user: User, db: AsyncSession) -> AvisoService:
    return AvisoService(db, tenant_id=user.tenant_id)


def _ack_service(user: User, db: AsyncSession) -> AcknowledgmentService:
    return AcknowledgmentService(db, tenant_id=user.tenant_id)


@router.get("", response_model=list[AvisoResponse])
async def list_avisos(
    _: None = Depends(require_permission("avisos:publicar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AvisoResponse]:
    service = _aviso_service(user, db)
    return await service.list_all()  # type: ignore[return-value]


@router.post("", response_model=AvisoResponse, status_code=status.HTTP_201_CREATED)
async def create_aviso(
    payload: AvisoCreate,
    request: Request,
    _: None = Depends(require_permission("avisos:publicar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoResponse:
    service = _aviso_service(user, db)
    aviso = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.AVISO_PUBLICAR,
        detalle={
            "aviso_id": str(aviso.id),
            "titulo": aviso.titulo,
            "alcance": aviso.alcance,
        },
    )

    return aviso  # type: ignore[return-value]


@router.get("/{aviso_id}", response_model=AvisoDetailResponse)
async def get_aviso(
    aviso_id: UUID,
    _: None = Depends(require_permission("avisos:publicar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoDetailResponse:
    service = _aviso_service(user, db)
    return await service.get(aviso_id)


@router.patch("/{aviso_id}", response_model=AvisoResponse)
async def update_aviso(
    aviso_id: UUID,
    payload: AvisoUpdate,
    request: Request,
    _: None = Depends(require_permission("avisos:publicar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvisoResponse:
    service = _aviso_service(user, db)
    aviso = await service.update(aviso_id, payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.AVISO_PUBLICAR,
        detalle={
            "aviso_id": str(aviso_id),
            "campos": list(payload.model_dump(exclude_unset=True).keys()),
        },
    )

    return aviso  # type: ignore[return-value]


@router.get("/mis-avisos", response_model=list[AvisoResponse])
async def mis_avisos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AvisoResponse]:
    service = _aviso_service(user, db)
    return await service.mis_avisos(user)  # type: ignore[return-value]


@router.post("/{aviso_id}/ack", response_model=AcknowledgmentResponse)
async def confirmar_ack(
    aviso_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AcknowledgmentResponse:
    service = _ack_service(user, db)
    ack = await service.confirmar(aviso_id, user.id)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.AVISO_ACK,
        detalle={"aviso_id": str(aviso_id)},
    )

    return ack  # type: ignore[return-value]
