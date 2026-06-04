"""
UsuarioRepository: Persistence layer for Usuario.

Inherits from TenantScopedRepository for automatic tenant isolation.
Provides multi-tenant-safe queries with email uniqueness checks.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import build_email_lookup
from app.models.usuario import Usuario
from app.repositories.base import TenantScopedRepository


class UsuarioRepository(TenantScopedRepository[Usuario]):
    """Repository for Usuario with tenant-scoped queries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str | None = None):
        """
        Initialize UsuarioRepository.

        If tenant_id is None, queries must provide it explicitly.
        """
        # Default to a placeholder if not provided; will be overridden per query
        if tenant_id is None:
            tenant_id = UUID("00000000-0000-0000-0000-000000000000")
        super().__init__(session, Usuario, tenant_id)

    async def create_user(
        self,
        tenant_id: UUID,
        nombre: str,
        apellidos: str,
        email: str,
        **extra_fields,
    ) -> Usuario:
        """
        Create a new usuario with email lookup hash.

        Args:
            tenant_id: Tenant UUID
            nombre: First name
            apellidos: Last name
            email: Email address (will be encrypted)
            **extra_fields: Additional fields (dni, cbu, etc.)

        Returns:
            Created Usuario instance
        """
        self.tenant_id = tenant_id
        # NOTE: email_lookup is NOT passed here because Usuario.__init__
        # already computes it from email. Passing it would cause a
        # TypeError (duplicate/unexpected keyword argument).
        usuario = await self.create(
            tenant_id=tenant_id,
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            **extra_fields,
        )
        return usuario

    async def find_by_id(
        self, usuario_id: UUID, tenant_id: UUID
    ) -> Usuario | None:
        """
        Find a usuario by ID, scoped to tenant.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID

        Returns:
            Usuario if found and belongs to tenant, else None
        """
        self.tenant_id = tenant_id
        return await self.get_by_id(usuario_id)

    async def find_by_email(
        self, email: str, tenant_id: UUID, include_deleted: bool = False
    ) -> Usuario | None:
        """
        Find a usuario by email (plaintext), scoped to tenant.

        Note: This requires decrypting all users, which is slow for large datasets.
        Prefer using email_lookup hash for uniqueness checks.

        Args:
            email: Email address (plaintext)
            tenant_id: Tenant UUID
            include_deleted: Whether to include soft-deleted users

        Returns:
            Usuario if found, else None
        """
        self.tenant_id = tenant_id
        email_lookup = build_email_lookup(email)
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted).where(
                Usuario.email_lookup == email_lookup
            )
        )
        return result.scalars().first()

    async def email_exists(
        self, email: str, tenant_id: UUID, exclude_usuario_id: UUID | None = None
    ) -> bool:
        """
        Check if email already exists in tenant (for uniqueness validation).

        Args:
            email: Email address (plaintext)
            tenant_id: Tenant UUID
            exclude_usuario_id: Exclude this usuario_id from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        self.tenant_id = tenant_id
        email_lookup = build_email_lookup(email)
        query = self._statement(include_deleted=False).where(
            Usuario.email_lookup == email_lookup
        )

        if exclude_usuario_id:
            query = query.where(Usuario.id != exclude_usuario_id)

        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def list_usuarios(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[Usuario]:
        """
        List usuarios in tenant with pagination.

        Args:
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum records to return
            include_deleted: Whether to include soft-deleted

        Returns:
            List of Usuario instances
        """
        self.tenant_id = tenant_id
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_usuario(
        self, usuario_id: UUID, tenant_id: UUID, data: dict
    ) -> Usuario | None:
        """
        Update a usuario (fields only, not email/PII).

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            data: Dict of fields to update

        Returns:
            Updated Usuario if found, else None
        """
        self.tenant_id = tenant_id
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            return None

        for key, value in data.items():
            if hasattr(usuario, key) and key not in ["email", "dni", "cbu", "cuil"]:
                setattr(usuario, key, value)

        await self.session.flush()
        await self.session.refresh(usuario)
        return usuario

    async def soft_delete_usuario(
        self, usuario_id: UUID, tenant_id: UUID
    ) -> Usuario | None:
        """
        Soft-delete a usuario.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID

        Returns:
            Deleted Usuario if found, else None
        """
        self.tenant_id = tenant_id
        return await self.soft_delete(usuario_id)
