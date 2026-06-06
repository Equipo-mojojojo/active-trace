from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.carrera import CarreraCreate, CarreraResponse, CarreraUpdate
from app.services.carrera_service import CarreraService

router = APIRouter(prefix="/api/admin", tags=["estructura"])


def build_service(db: AsyncSession, user: User) -> CarreraService:
    return CarreraService(db, tenant_id=user.tenant_id)


@router.get(
    "/carreras",
    response_model=list[CarreraResponse],
)
async def list_carreras(
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CarreraResponse]:
    service = build_service(db, user)
    return await service.list()  # type: ignore[return-value]


@router.get(
    "/carreras/{carrera_id}",
    response_model=CarreraResponse,
)
async def get_carrera(
    carrera_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    service = build_service(db, user)
    return await service.get(carrera_id)  # type: ignore[return-value]


@router.post(
    "/carreras",
    response_model=CarreraResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_carrera(
    payload: CarreraCreate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    service = build_service(db, user)
    return await service.create(payload)  # type: ignore[return-value]


@router.put(
    "/carreras/{carrera_id}",
    response_model=CarreraResponse,
)
async def update_carrera(
    carrera_id: UUID,
    payload: CarreraUpdate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    service = build_service(db, user)
    return await service.update(carrera_id, payload)  # type: ignore[return-value]


@router.delete(
    "/carreras/{carrera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_carrera(
    carrera_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_service(db, user)
    await service.delete(carrera_id)
