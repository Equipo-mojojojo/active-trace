"""
UsuarioService: Business logic for Usuario management.

Handles PII encryption/decryption, email uniqueness validation, and DTO conversions.
Enforces multi-tenancy isolation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    UsuarioResponseDTO,
)


class UsuarioAlreadyExistsError(Exception):
    """Raised when attempting to create a usuario with a duplicate email."""

    pass


class UsuarioNotFoundError(Exception):
    """Raised when a usuario is not found."""

    pass


class UsuarioService:
    """Service layer for Usuario management."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.repository = UsuarioRepository(session)

    async def create(
        self, request: UsuarioCreateRequest, tenant_id: UUID
    ) -> UsuarioResponseDTO:
        """
        Create a new usuario.

        Validates email uniqueness per tenant, encrypts PII, and returns response DTO.

        Args:
            request: UsuarioCreateRequest with nombre, apellidos, email, etc.
            tenant_id: Tenant UUID

        Returns:
            UsuarioResponseDTO (without PII)

        Raises:
            UsuarioAlreadyExistsError: If email already exists in tenant
        """
        # Check email uniqueness
        existing = await self.repository.email_exists(request.email, tenant_id)
        if existing:
            raise UsuarioAlreadyExistsError(
                f"Email {request.email} already exists in this tenant"
            )

        try:
            usuario = await self.repository.create_user(
                tenant_id=tenant_id,
                nombre=request.nombre,
                apellidos=request.apellidos,
                email=request.email,
                dni=request.dni,
                cuil=request.cuil,
                cbu=request.cbu,
                alias_cbu=request.alias_cbu,
                legajo=request.legajo,
            )
            await self.session.commit()
            return UsuarioResponseDTO.from_orm(usuario)
        except IntegrityError as e:
            await self.session.rollback()
            raise UsuarioAlreadyExistsError(
                f"Email uniqueness constraint violated: {str(e)}"
            ) from e

    async def get(
        self, usuario_id: UUID, tenant_id: UUID
    ) -> UsuarioResponseDTO | None:
        """
        Get a usuario by ID.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID

        Returns:
            UsuarioResponseDTO if found, else None
        """
        usuario = await self.repository.find_by_id(usuario_id, tenant_id)
        if not usuario:
            return None
        return UsuarioResponseDTO.from_orm(usuario)

    async def list(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UsuarioResponseDTO]:
        """
        List usuarios in tenant.

        Args:
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of UsuarioResponseDTO
        """
        usuarios = await self.repository.list_usuarios(
            tenant_id, skip=skip, limit=limit
        )
        return [UsuarioResponseDTO.from_orm(u) for u in usuarios]

    async def update(
        self, usuario_id: UUID, tenant_id: UUID, request: UsuarioUpdateRequest
    ) -> UsuarioResponseDTO | None:
        """
        Update a usuario (only nombre, apellidos).

        Note: Email and PII fields are not updatable.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            request: UsuarioUpdateRequest

        Returns:
            Updated UsuarioResponseDTO if found, else None
        """
        data = request.model_dump(exclude_unset=True)
        usuario = await self.repository.update_usuario(usuario_id, tenant_id, data)
        if not usuario:
            return None
        await self.session.commit()
        return UsuarioResponseDTO.from_orm(usuario)

    async def delete(self, usuario_id: UUID, tenant_id: UUID) -> None:
        """
        Soft-delete a usuario.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID

        Raises:
            UsuarioNotFoundError: If usuario not found
        """
        usuario = await self.repository.soft_delete_usuario(usuario_id, tenant_id)
        if not usuario:
            raise UsuarioNotFoundError(f"Usuario {usuario_id} not found")
        await self.session.commit()
