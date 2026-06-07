from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.role import (
    PermissionAssign,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.services.role_service import RoleService

router = APIRouter(prefix="/api/admin", tags=["admin-rbac"])


def build_role_service(db: AsyncSession, user: User) -> RoleService:
    return RoleService(db, tenant_id=user.tenant_id)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RoleResponse]:
    service = build_role_service(db, user)
    return await service.list_roles()  # type: ignore[return-value]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    service = build_role_service(db, user)
    return await service.create_role(payload)  # type: ignore[return-value]


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    service = build_role_service(db, user)
    return await service.update_role(role_id, payload)  # type: ignore[return-value]


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_role(
    role_id: UUID,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_role_service(db, user)
    await service.delete_role(role_id)


@router.get("/permisos", response_model=list[PermissionResponse])
async def list_permissions(
    modulo: str | None = None,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionResponse]:
    service = build_role_service(db, user)
    return await service.list_permissions(modulo=modulo)  # type: ignore[return-value]


@router.post(
    "/roles/{role_id}/permisos",
    status_code=status.HTTP_201_CREATED,
)
async def assign_permission(
    role_id: UUID,
    payload: PermissionAssign,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    service = build_role_service(db, user)
    await service.assign_permission(role_id, payload.permiso_id)
    return {"status": "ok"}


@router.delete(
    "/roles/{role_id}/permisos/{permiso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_permission(
    role_id: UUID,
    permiso_id: UUID,
    _: None = Depends(require_permission("rbac:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = build_role_service(db, user)
    await service.remove_permission(role_id, permiso_id)
