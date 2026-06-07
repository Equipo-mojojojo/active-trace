from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.cohorte import CohorteCreate, CohorteResponse, CohorteUpdate
from app.services.cohorte_service import CohorteService

router = APIRouter(prefix="/api/admin", tags=["estructura"])


def build_service(db: AsyncSession, user: User) -> CohorteService:
    return CohorteService(db, tenant_id=user.tenant_id)


@router.get(
    "/cohortes",
    response_model=list[CohorteResponse],
)
async def list_cohortes(
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CohorteResponse]:
    service = build_service(db, user)
    return await service.list()  # type: ignore[return-value]


@router.get(
    "/cohortes/{cohorte_id}",
    response_model=CohorteResponse,
)
async def get_cohorte(
    cohorte_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    service = build_service(db, user)
    return await service.get(cohorte_id)  # type: ignore[return-value]


@router.post(
    "/cohortes",
    response_model=CohorteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cohorte(
    payload: CohorteCreate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    service = build_service(db, user)
    return await service.create(payload)  # type: ignore[return-value]


@router.put(
    "/cohortes/{cohorte_id}",
    response_model=CohorteResponse,
)
async def update_cohorte(
    cohorte_id: UUID,
    payload: CohorteUpdate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    service = build_service(db, user)
    return await service.update(cohorte_id, payload)  # type: ignore[return-value]


@router.delete(
    "/cohortes/{cohorte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_cohorte(
    cohorte_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_service(db, user)
    await service.delete(cohorte_id)
