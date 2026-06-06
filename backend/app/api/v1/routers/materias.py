from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.materia import MateriaCreate, MateriaResponse, MateriaUpdate
from app.services.materia_service import MateriaService

router = APIRouter(prefix="/api/admin", tags=["estructura"])


def build_service(db: AsyncSession, user: User) -> MateriaService:
    return MateriaService(db, tenant_id=user.tenant_id)


@router.get(
    "/materias",
    response_model=list[MateriaResponse],
)
async def list_materias(
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MateriaResponse]:
    service = build_service(db, user)
    return await service.list()  # type: ignore[return-value]


@router.get(
    "/materias/{materia_id}",
    response_model=MateriaResponse,
)
async def get_materia(
    materia_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    service = build_service(db, user)
    return await service.get(materia_id)  # type: ignore[return-value]


@router.post(
    "/materias",
    response_model=MateriaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_materia(
    payload: MateriaCreate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    service = build_service(db, user)
    return await service.create(payload)  # type: ignore[return-value]


@router.put(
    "/materias/{materia_id}",
    response_model=MateriaResponse,
)
async def update_materia(
    materia_id: UUID,
    payload: MateriaUpdate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    service = build_service(db, user)
    return await service.update(materia_id, payload)  # type: ignore[return-value]


@router.delete(
    "/materias/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_materia(
    materia_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_service(db, user)
    await service.delete(materia_id)
