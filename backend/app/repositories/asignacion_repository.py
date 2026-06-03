"""
AsignacionRepository: Persistence layer for Asignacion.

Inherits from TenantScopedRepository for automatic tenant isolation.
Provides queries for vigency-filtered assignments.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import TenantScopedRepository


class AsignacionRepository(TenantScopedRepository[Asignacion]):
    """Repository for Asignacion with tenant-scoped queries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str | None = None):
        """
        Initialize AsignacionRepository.

        If tenant_id is None, queries must provide it explicitly.
        """
        if tenant_id is None:
            tenant_id = UUID("00000000-0000-0000-0000-000000000000")
        super().__init__(session, Asignacion, tenant_id)

    async def create_asignacion(
        self,
        tenant_id: UUID,
        usuario_id: UUID,
        rol: str,
        desde: date,
        hasta: date | None = None,
        **extra_fields,
    ) -> Asignacion:
        """
        Create a new asignacion.

        Args:
            tenant_id: Tenant UUID
            usuario_id: Usuario UUID
            rol: Role name (e.g., "PROFESOR")
            desde: Start date
            hasta: End date (optional, open-ended if None)
            **extra_fields: Additional fields (materia_id, carrera_id, etc.)

        Returns:
            Created Asignacion instance
        """
        self.tenant_id = tenant_id
        asignacion = await self.create(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            rol=rol,
            desde=desde,
            hasta=hasta,
            **extra_fields,
        )
        return asignacion

    async def find_by_id(
        self, asignacion_id: UUID, tenant_id: UUID
    ) -> Asignacion | None:
        """
        Find an asignacion by ID, scoped to tenant.

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID

        Returns:
            Asignacion if found and belongs to tenant, else None
        """
        self.tenant_id = tenant_id
        return await self.get_by_id(asignacion_id)

    async def find_vigent_for_user(
        self,
        usuario_id: UUID,
        tenant_id: UUID,
        rol: str | None = None,
        today: date | None = None,
    ) -> list[Asignacion]:
        """
        Find vigent assignments for a user.

        Vigent = desde <= today and (hasta is None or today < hasta)

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            rol: Optional role filter
            today: Reference date (defaults to date.today())

        Returns:
            List of vigent Asignacion instances
        """
        if today is None:
            today = date.today()

        self.tenant_id = tenant_id

        query = self._statement(include_deleted=False).where(
            and_(
                Asignacion.usuario_id == usuario_id,
                Asignacion.desde <= today,
            )
        )

        # Filter by estado_vigencia: hasta is None OR today < hasta
        query = query.where(
            (Asignacion.hasta.is_(None)) | (today < Asignacion.hasta)
        )

        if rol:
            query = query.where(Asignacion.rol == rol)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_all_for_user(
        self,
        usuario_id: UUID,
        tenant_id: UUID,
        include_deleted: bool = False,
    ) -> list[Asignacion]:
        """
        Find all assignments for a user (vigent + vencida + future).

        Args:
            usuario_id: Usuario UUID
            tenant_id: Tenant UUID
            include_deleted: Whether to include soft-deleted

        Returns:
            List of Asignacion instances
        """
        self.tenant_id = tenant_id
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted).where(
                Asignacion.usuario_id == usuario_id
            )
        )
        return list(result.scalars().all())

    async def find_by_context(
        self,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[Asignacion]:
        """
        Find assignments by context (materia, carrera, cohorte).

        Args:
            tenant_id: Tenant UUID
            materia_id: Optional materia UUID filter
            carrera_id: Optional carrera UUID filter
            cohorte_id: Optional cohorte UUID filter

        Returns:
            List of Asignacion instances
        """
        self.tenant_id = tenant_id

        query = self._statement(include_deleted=False)

        if materia_id:
            query = query.where(Asignacion.materia_id == materia_id)
        if carrera_id:
            query = query.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id:
            query = query.where(Asignacion.cohorte_id == cohorte_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_asignacion(
        self, asignacion_id: UUID, tenant_id: UUID, data: dict
    ) -> Asignacion | None:
        """
        Update an asignacion (responsable_id, hasta only).

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID
            data: Dict of fields to update

        Returns:
            Updated Asignacion if found, else None
        """
        self.tenant_id = tenant_id
        asignacion = await self.get_by_id(asignacion_id)
        if not asignacion:
            return None

        # Only allow certain fields to be updated
        for key in ["responsable_id", "hasta"]:
            if key in data:
                setattr(asignacion, key, data[key])

        await self.session.flush()
        await self.session.refresh(asignacion)
        return asignacion

    async def soft_delete_asignacion(
        self, asignacion_id: UUID, tenant_id: UUID
    ) -> Asignacion | None:
        """
        Soft-delete an asignacion.

        Args:
            asignacion_id: Asignacion UUID
            tenant_id: Tenant UUID

        Returns:
            Deleted Asignacion if found, else None
        """
        self.tenant_id = tenant_id
        return await self.soft_delete(asignacion_id)

    async def list_asignaciones(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[Asignacion]:
        """
        List asignaciones in tenant with pagination.

        Args:
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum records to return
            include_deleted: Whether to include soft-deleted

        Returns:
            List of Asignacion instances
        """
        self.tenant_id = tenant_id
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
