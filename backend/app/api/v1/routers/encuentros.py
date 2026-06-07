from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.encuentros import (
    EncuentroExportLMS,
    InstanciaEncuentroCreate,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
    SlotEncuentroUpdate,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.encuentro_export_service import EncuentroExportService
from app.services.instancia_encuentro_service import (
    InstanciaEncuentroService,
)
from app.services.slot_encuentro_service import SlotEncuentroService

router = APIRouter(prefix="/api/v1/encuentros", tags=["encuentros"])


def _slot_service(user: User, db: AsyncSession) -> SlotEncuentroService:
    return SlotEncuentroService(db, tenant_id=user.tenant_id)


def _instancia_service(
    user: User, db: AsyncSession,
) -> InstanciaEncuentroService:
    return InstanciaEncuentroService(db, tenant_id=user.tenant_id)


def _export_service(user: User, db: AsyncSession) -> EncuentroExportService:
    return EncuentroExportService(db, tenant_id=user.tenant_id)


# ── Slots ──────────────────────────────────────────────────────────────


@router.get(
    "/slots",
    response_model=list[SlotEncuentroResponse],
)
async def list_slots(
    _: None = Depends(require_permission("encuentros:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SlotEncuentroResponse]:
    service = _slot_service(user, db)
    return await service.list()  # type: ignore[return-value]


@router.post(
    "/slots",
    response_model=SlotEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_slot(
    payload: SlotEncuentroCreate,
    request: Request,
    _: None = Depends(require_permission("encuentros:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlotEncuentroResponse:
    service = _slot_service(user, db)
    slot = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.ENCUENTRO_CREAR,
        materia_id=payload.materia_id,
        detalle={
            "slot_id": str(slot.id),
            "tipo": "recurrente" if payload.cant_semanas > 0 else "fecha_unica",
            "cant_semanas": payload.cant_semanas,
        },
    )

    return slot  # type: ignore[return-value]


@router.get(
    "/slots/{slot_id}",
    response_model=SlotEncuentroResponse,
)
async def get_slot(
    slot_id: UUID,
    _: None = Depends(require_permission("encuentros:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlotEncuentroResponse:
    service = _slot_service(user, db)
    return await service.get(slot_id)  # type: ignore[return-value]


@router.patch(
    "/slots/{slot_id}",
    response_model=SlotEncuentroResponse,
)
async def update_slot(
    slot_id: UUID,
    payload: SlotEncuentroUpdate,
    request: Request,
    _: None = Depends(require_permission("encuentros:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlotEncuentroResponse:
    service = _slot_service(user, db)
    slot = await service.update(slot_id, payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.ENCUENTRO_EDITAR,
        materia_id=slot.materia_id,
        detalle={"slot_id": str(slot_id), "campos": list(payload.model_dump(exclude_unset=True).keys())},
    )

    return slot  # type: ignore[return-value]


@router.delete(
    "/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_slot(
    slot_id: UUID,
    _: None = Depends(require_permission("encuentros:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = _slot_service(user, db)
    await service.delete(slot_id)


# ── Instancias ─────────────────────────────────────────────────────────


@router.get(
    "/instancias",
    response_model=list[InstanciaEncuentroResponse],
)
async def list_instancias(
    materia_id: UUID | None = None,
    slot_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    estado: str | None = None,
    _: None = Depends(require_permission("encuentros:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InstanciaEncuentroResponse]:
    service = _instancia_service(user, db)
    return await service.list(
        materia_id=materia_id,
        slot_id=slot_id,
        desde=desde,
        hasta=hasta,
        estado=estado,
    )  # type: ignore[return-value]


@router.post(
    "/instancias",
    response_model=InstanciaEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_instancia(
    payload: InstanciaEncuentroCreate,
    request: Request,
    _: None = Depends(require_permission("encuentros:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaEncuentroResponse:
    service = _instancia_service(user, db)
    instancia = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.ENCUENTRO_CREAR,
        materia_id=payload.materia_id,
        detalle={"instancia_id": str(instancia.id), "tipo": "independiente"},
    )

    return instancia  # type: ignore[return-value]


@router.get(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroResponse,
)
async def get_instancia(
    instancia_id: UUID,
    _: None = Depends(require_permission("encuentros:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaEncuentroResponse:
    service = _instancia_service(user, db)
    return await service.get(instancia_id)  # type: ignore[return-value]


@router.patch(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroResponse,
)
async def update_instancia(
    instancia_id: UUID,
    payload: InstanciaEncuentroUpdate,
    request: Request,
    _: None = Depends(require_permission("encuentros:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaEncuentroResponse:
    service = _instancia_service(user, db)
    instancia = await service.update(instancia_id, payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.ENCUENTRO_EDITAR,
        materia_id=instancia.materia_id,
        detalle={
            "instancia_id": str(instancia_id),
            "campos": list(payload.model_dump(exclude_unset=True).keys()),
        },
    )

    return instancia  # type: ignore[return-value]


# ── Export LMS ─────────────────────────────────────────────────────────


@router.get(
    "/{materia_id}/export-lms",
    response_model=EncuentroExportLMS,
)
async def export_lms(
    materia_id: UUID,
    _: None = Depends(require_permission("encuentros:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EncuentroExportLMS:
    service = _export_service(user, db)
    return await service.generate_html(materia_id)
