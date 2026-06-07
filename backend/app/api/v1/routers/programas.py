from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.programa_materia import (
    ProgramaMateriaCreate,
    ProgramaMateriaResponse,
    ProgramaMateriaUpdate,
)
from app.services.programa_materia_service import ProgramaMateriaService

router = APIRouter(prefix="/api/admin", tags=["estructura"])


def build_service(db: AsyncSession, user: User) -> ProgramaMateriaService:
    return ProgramaMateriaService(db, tenant_id=user.tenant_id)


@router.get(
    "/programas",
    response_model=list[ProgramaMateriaResponse],
)
async def list_programas(
    materia_id: UUID | None = None,
    carrera_id: UUID | None = None,
    cohorte_id: UUID | None = None,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgramaMateriaResponse]:
    service = build_service(db, user)
    return await service.list(  # type: ignore[return-value]
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )


@router.get(
    "/programas/{programa_id}",
    response_model=ProgramaMateriaResponse,
)
async def get_programa(
    programa_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramaMateriaResponse:
    service = build_service(db, user)
    return await service.get(programa_id)  # type: ignore[return-value]


@router.post(
    "/programas",
    response_model=ProgramaMateriaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_programa(
    payload: ProgramaMateriaCreate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramaMateriaResponse:
    service = build_service(db, user)
    return await service.create(payload)  # type: ignore[return-value]


@router.put(
    "/programas/{programa_id}",
    response_model=ProgramaMateriaResponse,
)
async def update_programa(
    programa_id: UUID,
    payload: ProgramaMateriaUpdate,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgramaMateriaResponse:
    service = build_service(db, user)
    return await service.update(programa_id, payload)  # type: ignore[return-value]


@router.delete(
    "/programas/{programa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_programa(
    programa_id: UUID,
    _: None = Depends(require_permission("estructura:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_service(db, user)
    await service.delete(programa_id)
