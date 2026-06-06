from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCreate,
    TareaResponse,
    TareaUpdate,
)
from app.services.audit_service import AuditService, get_request_context
from app.services.comentario_tarea_service import ComentarioTareaService
from app.services.tarea_service import TareaService

router = APIRouter(prefix="/api/v1/tareas", tags=["tareas"])


def _tarea_service(user: User, db: AsyncSession) -> TareaService:
    return TareaService(db, tenant_id=user.tenant_id, user_id=user.id)


def _comentario_service(user: User, db: AsyncSession) -> ComentarioTareaService:
    return ComentarioTareaService(db, tenant_id=user.tenant_id, user_id=user.id)


@router.get("/mias", response_model=list[TareaResponse])
async def mis_tareas(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TareaResponse]:
    service = _tarea_service(user, db)
    return await service.list_mias()  # type: ignore[return-value]


@router.get("", response_model=list[TareaResponse])
async def list_tareas(
    estado: str | None = Query(None),
    materia_id: UUID | None = Query(None),
    asignado_a: UUID | None = Query(None),
    asignado_por: UUID | None = Query(None),
    q: str | None = Query(None),
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TareaResponse]:
    service = _tarea_service(user, db)
    return await service.list_all(
        estado=estado,
        materia_id=materia_id,
        asignado_a=asignado_a,
        asignado_por=asignado_por,
        q=q,
    )  # type: ignore[return-value]


@router.post("", response_model=TareaResponse, status_code=status.HTTP_201_CREATED)
async def create_tarea(
    payload: TareaCreate,
    request: Request,
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    service = _tarea_service(user, db)
    tarea = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.TAREA_CREAR,
        detalle={
            "tarea_id": str(tarea.id),
            "asignado_a": str(tarea.asignado_a),
        },
    )

    return tarea  # type: ignore[return-value]


@router.get("/{tarea_id}", response_model=TareaResponse)
async def get_tarea(
    tarea_id: UUID,
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    service = _tarea_service(user, db)
    return await service.get(tarea_id)  # type: ignore[return-value]


@router.patch("/{tarea_id}", response_model=TareaResponse)
async def update_tarea(
    tarea_id: UUID,
    payload: TareaUpdate,
    request: Request,
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TareaResponse:
    service = _tarea_service(user, db)
    tarea = await service.update(tarea_id, payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.TAREA_CREAR,
        detalle={
            "tarea_id": str(tarea_id),
            "campos": list(payload.model_dump(exclude_unset=True).keys()),
        },
    )

    return tarea  # type: ignore[return-value]


@router.get("/{tarea_id}/comentarios", response_model=list[ComentarioResponse])
async def list_comentarios(
    tarea_id: UUID,
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComentarioResponse]:
    service = _comentario_service(user, db)
    return await service.listar(tarea_id)  # type: ignore[return-value]


@router.post("/{tarea_id}/comentarios", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
async def create_comentario(
    tarea_id: UUID,
    payload: ComentarioCreate,
    request: Request,
    _: None = Depends(require_permission("tareas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComentarioResponse:
    service = _comentario_service(user, db)
    comentario = await service.agregar(tarea_id, payload.texto)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.TAREA_COMENTAR,
        detalle={
            "tarea_id": str(tarea_id),
            "comentario_id": str(comentario.id),
        },
    )

    return comentario  # type: ignore[return-value]
