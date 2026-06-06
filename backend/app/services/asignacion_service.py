"""
AsignacionService: Business logic for Asignacion management.

Handles vigency filtering, multi-role aggregation, and DTO conversions.
Enforces multi-tenancy isolation.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.asignacion_schema import (
    AsignacionCreateRequest,
    AsignacionUpdateRequest,
    AsignacionResponseDTO,
)


class AsignacionValidationError(Exception):
    """Raised on validation errors."""

    pass


class AsignacionNotFoundError(Exception):
    """Raised when an asignacion is not found."""

    pass


class AsignacionService:
    """Service layer for Asignacion management."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.repository = AsignacionRepository(session)
        self.usuario_repository = UsuarioRepository(session)

    async def create(
        self, request: AsignacionCreateRequest, tenant_id: UUID
    ) -> AsignacionResponseDTO:
        """
        Create a new asignacion.

        Validates:
        - Usuario exists and belongs to tenant
        - Responsable (if provided) is different from usuario and exists
        - desde <= hasta (if hasta provided)

        Args:
            request: AsignacionCreateRequest
            tenant_id: Tenant UUID

        Returns:
            AsignacionResponseDTO

        Raises:
            AsignacionValidationError: If validation fails
        """
        # Validate usuario exists
        usuario = await self.usuario_repository.find_by_id(
            request.usuario_id, tenant_id
        )
        if not usuario:
            raise AsignacionValidationError(
                f"Usuario {request.usuario_id} not found in tenant {tenant_id}"
            )

        # Validate responsable_id if provided
        if request.responsable_id:
            if request.responsable_id == request.usuario_id:
                raise AsignacionValidationError(
                    "A usuario cannot be their own responsable"
                )

            responsable = await self.usuario_repository.find_by_id(
                request.responsable_id, tenant_id
            )
            if not responsable:
                raise AsignacionValidationError(
                    f"Responsable {request.responsable_id} not found in tenant {tenant_id}"
                )

        # Validate dates
        if request.hasta and request.desde > request.hasta:
            raise AsignacionValidationError(
                f"desde ({request.desde}) cannot be after hasta ({request.hasta})"
            )

        asignacion = await self.repository.create_asignacion(
            tenant_id=tenant_id,
            usuario_id=request.usuario_id,
            rol=request.rol,
            desde=request.desde,
            hasta=request.hasta,
            materia_id=request.materia_id,
            carrera_id=request.carrera_id,
            cohorte_id=request.cohorte_id,
            comisiones=request.comisiones,
            responsable_id=request.responsable_id,
        )
        await self.session.commit()
        return AsignacionResponseDTO.from_orm(asignacion)

    async def get(
        self, asignacion_id: UUID, tenant_id: UUID
    ) -> AsignacionResponseDTO | None:
        """
        Get an asignacion by ID.

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID

        Returns:
            AsignacionResponseDTO if found, else None
        """
        asignacion = await self.repository.find_by_id(asignacion_id, tenant_id)
        if not asignacion:
            return None
        return AsignacionResponseDTO.from_orm(asignacion)

    async def list_vigent(
        self,
        usuario_id: UUID,
        tenant_id: UUID,
        rol: str | None = None,
        materia_id: UUID | None = None,
        today: date | None = None,
    ) -> list[AsignacionResponseDTO]:
        """
        List vigent assignments for a usuario.

        Vigent = desde <= today and (hasta is None or today < hasta)

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            rol: Optional role filter
            materia_id: Optional materia filter
            today: Reference date (defaults to date.today())

        Returns:
            List of AsignacionResponseDTO
        """
        asignaciones = await self.repository.find_vigent_for_user(
            usuario_id, tenant_id, rol=rol, today=today
        )

        if materia_id:
            asignaciones = [a for a in asignaciones if a.materia_id == materia_id]

        return [AsignacionResponseDTO.from_orm(a) for a in asignaciones]

    async def list_all(
        self,
        usuario_id: UUID,
        tenant_id: UUID,
        estado_vigencia: str = "todas",
    ) -> list[AsignacionResponseDTO]:
        """
        List all assignments for a usuario, optionally filtered by vigency.

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            estado_vigencia: "todas", "vigente", "vencida", or "futura"

        Returns:
            List of AsignacionResponseDTO
        """
        asignaciones = await self.repository.find_all_for_user(
            usuario_id, tenant_id
        )

        today = date.today()

        if estado_vigencia == "vigente":
            asignaciones = [
                a
                for a in asignaciones
                if a.estado_vigencia == "Vigente"
            ]
        elif estado_vigencia == "vencida":
            asignaciones = [
                a
                for a in asignaciones
                if a.estado_vigencia == "Vencida"
            ]
        elif estado_vigencia == "futura":
            asignaciones = [
                a
                for a in asignaciones
                if a.estado_vigencia == "Futura"
            ]

        return [AsignacionResponseDTO.from_orm(a) for a in asignaciones]

    async def update(
        self, asignacion_id: UUID, tenant_id: UUID, request: AsignacionUpdateRequest
    ) -> AsignacionResponseDTO | None:
        """
        Update an asignacion (responsable_id, hasta only).

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID
            request: AsignacionUpdateRequest

        Returns:
            Updated AsignacionResponseDTO if found, else None

        Raises:
            AsignacionValidationError: If validation fails
        """
        # Validate responsable_id if provided
        if request.responsable_id:
            asignacion = await self.repository.find_by_id(asignacion_id, tenant_id)
            if not asignacion:
                raise AsignacionNotFoundError(f"Asignacion {asignacion_id} not found")

            if request.responsable_id == asignacion.usuario_id:
                raise AsignacionValidationError(
                    "A usuario cannot be their own responsable"
                )

            responsable = await self.usuario_repository.find_by_id(
                request.responsable_id, tenant_id
            )
            if not responsable:
                raise AsignacionValidationError(
                    f"Responsable {request.responsable_id} not found in tenant {tenant_id}"
                )

        data = request.model_dump(exclude_unset=True)
        asignacion = await self.repository.update_asignacion(
            asignacion_id, tenant_id, data
        )
        if not asignacion:
            raise AsignacionNotFoundError(f"Asignacion {asignacion_id} not found")

        await self.session.commit()
        return AsignacionResponseDTO.from_orm(asignacion)

    async def delete(self, asignacion_id: UUID, tenant_id: UUID) -> None:
        """
        Soft-delete an asignacion.

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID

        Raises:
            AsignacionNotFoundError: If asignacion not found
        """
        asignacion = await self.repository.soft_delete_asignacion(
            asignacion_id, tenant_id
        )
        if not asignacion:
            raise AsignacionNotFoundError(f"Asignacion {asignacion_id} not found")
        await self.session.commit()
