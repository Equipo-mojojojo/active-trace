from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.inbox import HiloOut, MensajeCreate, MensajeInternoOut, MensajeResponder
from app.services.inbox_service import (
    InboxConflictError,
    InboxForbiddenError,
    InboxNotFoundError,
    InboxService,
)

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


def _service(user: User, db: AsyncSession) -> InboxService:
    return InboxService(db, tenant_id=user.tenant_id)


@router.get("", response_model=list[HiloOut])
async def listar_hilos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HiloOut]:
    service = _service(user, db)
    hilos = await service.listar_hilos(user.id)
    return [HiloOut(**vars(h)) for h in hilos]


@router.post("", response_model=MensajeInternoOut, status_code=status.HTTP_201_CREATED)
async def iniciar_hilo(
    payload: MensajeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MensajeInternoOut:
    service = _service(user, db)
    try:
        msg = await service.iniciar_hilo(
            remitente_id=user.id,
            destinatario_id=payload.destinatario_id,
            asunto=payload.asunto,
            cuerpo=payload.cuerpo,
        )
    except InboxConflictError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except InboxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return msg  # type: ignore[return-value]


@router.get("/{hilo_id}", response_model=list[MensajeInternoOut])
async def leer_hilo(
    hilo_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MensajeInternoOut]:
    service = _service(user, db)
    try:
        return await service.leer_hilo(hilo_id, user.id)  # type: ignore[return-value]
    except InboxForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InboxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{hilo_id}/responder", response_model=MensajeInternoOut, status_code=status.HTTP_201_CREATED)
async def responder_hilo(
    hilo_id: UUID,
    payload: MensajeResponder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MensajeInternoOut:
    service = _service(user, db)
    try:
        return await service.responder(hilo_id, user.id, payload.cuerpo)  # type: ignore[return-value]
    except InboxForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InboxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
