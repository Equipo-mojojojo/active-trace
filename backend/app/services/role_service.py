from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import invalidate_permission_cache_for_role
from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    """Business logic for role and permission management."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = RoleRepository(db)
        self.tenant_id = tenant_id

    async def list_roles(self) -> list[Role]:
        return await self.repository.get_roles_by_tenant(self.tenant_id)

    async def get_role(self, role_id: UUID) -> Role:
        role = await self.repository.get_role_by_id(role_id, self.tenant_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado",
            )
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        existing = await self.repository.get_role_by_name(data.nombre, self.tenant_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un rol con el nombre '{data.nombre}'",
            )
        return await self.repository.create_role(
            tenant_id=self.tenant_id,
            nombre=data.nombre,
            descripcion=data.descripcion,
        )

    async def update_role(self, role_id: UUID, data: RoleUpdate) -> Role:
        role = await self.get_role(role_id)

        if data.nombre is not None and data.nombre != role.nombre:
            existing = await self.repository.get_role_by_name(data.nombre, self.tenant_id)
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un rol con el nombre '{data.nombre}'",
                )

        return await self.repository.update_role(
            role,
            nombre=data.nombre,
            descripcion=data.descripcion,
        )

    async def delete_role(self, role_id: UUID) -> None:
        role = await self.get_role(role_id)
        await self.repository.soft_delete_role(role)

    async def list_permissions(self, modulo: str | None = None) -> list:
        return await self.repository.get_permissions_by_tenant(
            self.tenant_id, modulo=modulo
        )

    async def assign_permission(self, role_id: UUID, permiso_id: UUID) -> None:
        role = await self.get_role(role_id)
        _perm = await self.repository.get_permission_by_id(permiso_id, self.tenant_id)
        if _perm is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permiso no encontrado",
            )

        await self.repository.assign_permission_to_role(
            role_id=role.id,
            permiso_id=permiso_id,
            tenant_id=self.tenant_id,
        )
        invalidate_permission_cache_for_role(self.tenant_id, role.nombre)

    async def remove_permission(self, role_id: UUID, permiso_id: UUID) -> None:
        role = await self.get_role(role_id)
        removed = await self.repository.remove_permission_from_role(
            role_id=role.id,
            permiso_id=permiso_id,
            tenant_id=self.tenant_id,
        )
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El rol no tiene ese permiso asignado",
            )
        invalidate_permission_cache_for_role(self.tenant_id, role.nombre)
