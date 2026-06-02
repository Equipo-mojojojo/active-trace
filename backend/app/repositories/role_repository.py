from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


class RoleRepository:
    """Repository for RBAC operations.

    Uses direct queries rather than TenantScopedRepository because
    permission resolution spans multiple models (Role, Permission,
    RolePermission) and needs custom join logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_roles_by_tenant(self, tenant_id: UUID) -> list[Role]:
        result = await self.session.execute(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def get_role_by_id(self, role_id: UUID, tenant_id: UUID) -> Role | None:
        result = await self.session.execute(
            select(Role).where(
                Role.id == role_id,
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_role_by_name(self, nombre: str, tenant_id: UUID) -> Role | None:
        result = await self.session.execute(
            select(Role).where(
                Role.nombre == nombre,
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_role(self, tenant_id: UUID, nombre: str, descripcion: str | None = None) -> Role:
        role = Role(tenant_id=tenant_id, nombre=nombre, descripcion=descripcion)
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update_role(self, role: Role, nombre: str | None = None, descripcion: str | None = None) -> Role:
        if nombre is not None:
            role.nombre = nombre
        if descripcion is not None:
            role.descripcion = descripcion
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def soft_delete_role(self, role: Role) -> None:
        role.mark_deleted()
        await self.session.flush()

    async def get_permissions_by_tenant(self, tenant_id: UUID, modulo: str | None = None) -> list[Permission]:
        statement = select(Permission).where(Permission.tenant_id == tenant_id)

        if modulo is not None:
            statement = statement.where(Permission.modulo == modulo)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_permission_by_id(self, permiso_id: UUID, tenant_id: UUID) -> Permission | None:
        result = await self.session.execute(
            select(Permission).where(
                Permission.id == permiso_id,
                Permission.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_role_permissions(self, role_id: UUID, tenant_id: UUID) -> list[Permission]:
        """Return all permissions assigned to a given role."""
        result = await self.session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permiso_id == Permission.id)
            .where(
                RolePermission.rol_id == role_id,
                RolePermission.tenant_id == tenant_id,
                Permission.tenant_id == tenant_id,
            )
        )
        return list(result.scalars().all())

    async def get_effective_permission_codes(self, user_id: UUID, tenant_id: UUID) -> set[str]:
        """Return the set of permission codes for all roles of a user.

        This queries the RolePermission join table using the user's
        roles from User.roles (JSON) — which is the source of truth
        until C-07 formalizes the assignment model.
        """
        from app.models.user import User

        user_result = await self.session.execute(
            select(User.roles).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        )
        user_roles = user_result.scalar_one_or_none()

        if not user_roles:
            return set()

        result = await self.session.execute(
            select(Permission.codigo)
            .join(RolePermission, RolePermission.permiso_id == Permission.id)
            .join(Role, Role.id == RolePermission.rol_id)
            .where(
                Role.nombre.in_(user_roles),
                Role.tenant_id == tenant_id,
                Permission.tenant_id == tenant_id,
                RolePermission.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
        )
        return set(result.scalars().all())

    async def assign_permission_to_role(
        self, role_id: UUID, permiso_id: UUID, tenant_id: UUID
    ) -> RolePermission:
        rp = RolePermission(rol_id=role_id, permiso_id=permiso_id, tenant_id=tenant_id)
        self.session.add(rp)
        await self.session.flush()
        await self.session.refresh(rp)
        return rp

    async def remove_permission_from_role(
        self, role_id: UUID, permiso_id: UUID, tenant_id: UUID
    ) -> bool:
        result = await self.session.execute(
            select(RolePermission).where(
                RolePermission.rol_id == role_id,
                RolePermission.permiso_id == permiso_id,
                RolePermission.tenant_id == tenant_id,
            )
        )
        rp = result.scalar_one_or_none()
        if rp is None:
            return False
        await self.session.delete(rp)
        await self.session.flush()
        return True
