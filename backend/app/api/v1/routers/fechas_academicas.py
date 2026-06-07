from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.enums import TipoEvaluacion
from app.models.user import User
from app.schemas.fecha_academica import (
    FechaAcademicaCreate,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
)
from app.services.fecha_academica_service import FechaAcademicaService

router = APIRouter(prefix="/api/admin", tags=["estructura"])


def build_service(db: AsyncSession, user: User) -> FechaAcademicaService:
    return FechaAcademicaService(db, tenant_id=user.tenant_id)


@router.get(
    "/fechas-academicas",
    response_model=list[FechaAcademicaResponse],
)
async def list_fechas_academicas(
    materia_id: UUID | None = None,
    cohorte_id: UUID | None = None,
    tipo: TipoEvaluacion | None = None,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FechaAcademicaResponse]:
    service = build_service(db, user)
    return await service.list(  # type: ignore[return-value]
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=tipo,
    )


@router.get(
    "/fechas-academicas/{fecha_id}",
    response_model=FechaAcademicaResponse,
)
async def get_fecha_academica(
    fecha_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FechaAcademicaResponse:
    service = build_service(db, user)
    return await service.get(fecha_id)  # type: ignore[return-value]


@router.post(
    "/fechas-academicas",
    response_model=FechaAcademicaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fecha_academica(
    payload: FechaAcademicaCreate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FechaAcademicaResponse:
    service = build_service(db, user)
    return await service.create(payload)  # type: ignore[return-value]


@router.put(
    "/fechas-academicas/{fecha_id}",
    response_model=FechaAcademicaResponse,
)
async def update_fecha_academica(
    fecha_id: UUID,
    payload: FechaAcademicaUpdate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FechaAcademicaResponse:
    service = build_service(db, user)
    return await service.update(fecha_id, payload)  # type: ignore[return-value]


@router.delete(
    "/fechas-academicas/{fecha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_fecha_academica(
    fecha_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_service(db, user)
    await service.delete(fecha_id)
