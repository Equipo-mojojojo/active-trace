from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.perfil import PerfilOut, PerfilUpdate
from app.services.perfil_service import PerfilConflictError, PerfilNotFoundError, PerfilService

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _service(user: User, db: AsyncSession) -> PerfilService:
    return PerfilService(db, tenant_id=user.tenant_id)


@router.get("", response_model=PerfilOut)
async def get_perfil(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerfilOut:
    service = _service(user, db)
    try:
        return await service.get_perfil(user.id)  # type: ignore[return-value]
    except PerfilNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("", response_model=PerfilOut)
async def update_perfil(
    payload: PerfilUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerfilOut:
    service = _service(user, db)
    data = payload.model_dump(exclude_none=True)
    try:
        return await service.update_perfil(user.id, data)  # type: ignore[return-value]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PerfilNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
