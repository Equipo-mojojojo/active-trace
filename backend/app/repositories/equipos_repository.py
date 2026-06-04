"""
EquiposRepository: Persistence layer for equipo-docente operations (C-08).

Wraps AsignacionRepository logic with domain-specific operations:
- listar_por_usuario: view for docentes (mis-equipos)
- listar_por_tenant: view for coordinadores (all assignments)
- crear_masivo: bulk creation in one flush
- clonar_equipo: duplicate vigent assignments to a new cohorte
- actualizar_vigencia_equipo: bulk update desde/hasta (supports dry_run)

All queries are tenant-scoped by default (multi-tenancy rule hard coded).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import TenantScopedRepository


class EquiposRepository(TenantScopedRepository[Asignacion]):
    """Repository for equipo-docente domain operations, scoped per tenant."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, Asignacion, tenant_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _vigentes_stmt(self, today: date | None = None):
        """Base statement filtered to vigent (active) asignaciones."""
        if today is None:
            today = date.today()
        return self._statement(include_deleted=False).where(
            and_(
                Asignacion.desde <= today,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today),
            )
        )

    # ------------------------------------------------------------------
    # 1.1 Query methods
    # ------------------------------------------------------------------

    async def listar_por_usuario(
        self,
        usuario_id: UUID,
        filtros: dict,
        today: date | None = None,
    ) -> list[Asignacion]:
        """
        Return all assignments for a user within the active tenant.

        Scope: tenant_id always enforced (TenantScopedRepository._statement).
        Filtros soportados: estado, materia_id, rol, carrera_id, cohorte_id.

        Args:
            usuario_id: UUID of the authenticated user.
            filtros: Dict of optional filter keys.
            today: Override for date.today() (injection for tests).

        Returns:
            List of Asignacion instances.
        """
        if today is None:
            today = date.today()

        stmt = self._statement(include_deleted=False).where(
            Asignacion.usuario_id == usuario_id
        )

        if filtros.get("materia_id"):
            stmt = stmt.where(Asignacion.materia_id == filtros["materia_id"])
        if filtros.get("rol"):
            stmt = stmt.where(Asignacion.rol == filtros["rol"])
        if filtros.get("carrera_id"):
            stmt = stmt.where(Asignacion.carrera_id == filtros["carrera_id"])
        if filtros.get("cohorte_id"):
            stmt = stmt.where(Asignacion.cohorte_id == filtros["cohorte_id"])

        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())

        # Filter by derived estado_vigencia AFTER loading (computed property)
        estado = filtros.get("estado")
        if estado:
            asignaciones = [a for a in asignaciones if a.estado_vigencia == estado]

        return asignaciones

    async def listar_por_tenant(
        self,
        filtros: dict,
        today: date | None = None,
    ) -> list[Asignacion]:
        """
        Return all assignments in the active tenant with optional filters.

        For COORDINADOR/ADMIN view.

        Args:
            filtros: Dict of optional filter keys (same as listar_por_usuario).
            today: Override for date.today().

        Returns:
            List of Asignacion instances.
        """
        if today is None:
            today = date.today()

        stmt = self._statement(include_deleted=False)

        if filtros.get("materia_id"):
            stmt = stmt.where(Asignacion.materia_id == filtros["materia_id"])
        if filtros.get("rol"):
            stmt = stmt.where(Asignacion.rol == filtros["rol"])
        if filtros.get("carrera_id"):
            stmt = stmt.where(Asignacion.carrera_id == filtros["carrera_id"])
        if filtros.get("cohorte_id"):
            stmt = stmt.where(Asignacion.cohorte_id == filtros["cohorte_id"])
        if filtros.get("usuario_id"):
            stmt = stmt.where(Asignacion.usuario_id == filtros["usuario_id"])

        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())

        estado = filtros.get("estado")
        if estado:
            asignaciones = [a for a in asignaciones if a.estado_vigencia == estado]

        return asignaciones

    # ------------------------------------------------------------------
    # 1.1 Bulk creation
    # ------------------------------------------------------------------

    async def crear_masivo(self, datos: list[dict]) -> list[Asignacion]:
        """
        Create multiple Asignacion rows in a single flush.

        Each dict must include: tenant_id, usuario_id, rol, desde.
        Optional: hasta, materia_id, carrera_id, cohorte_id, comisiones, responsable_id.

        The caller is responsible for committing (or rolling back on error).

        Args:
            datos: List of dicts with Asignacion field values.

        Returns:
            List of created Asignacion instances (flushed, not committed).
        """
        created: list[Asignacion] = []
        for item in datos:
            asig = Asignacion(**item)
            self.session.add(asig)
            created.append(asig)

        await self.session.flush()
        for asig in created:
            await self.session.refresh(asig)
        return created

    # ------------------------------------------------------------------
    # 1.1 Clone
    # ------------------------------------------------------------------

    async def clonar_equipo(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id_origen: UUID,
        cohorte_id_destino: UUID,
        nueva_desde: date,
        nueva_hasta: date | None = None,
        today: date | None = None,
    ) -> list[Asignacion]:
        """
        Duplicate all vigent assignments of an origin team to a destination cohorte.

        Design D3: Vigent assignments are duplicated with new cohorte_id and dates.
        Assignments with hasta=NULL (open) receive nueva_hasta from the request.
        Origin assignments are NOT modified.

        Args:
            materia_id: Context materia UUID.
            carrera_id: Context carrera UUID.
            cohorte_id_origen: Source cohorte UUID.
            cohorte_id_destino: Target cohorte UUID.
            nueva_desde: Start date for cloned assignments.
            nueva_hasta: End date for cloned assignments (None = open).
            today: Override date.today() for tests.

        Returns:
            List of created (cloned) Asignacion instances.
        """
        if today is None:
            today = date.today()

        # Fetch vigent assignments from origin team (Design D5: derived in Python)
        stmt = self._statement(include_deleted=False).where(
            and_(
                Asignacion.materia_id == materia_id,
                Asignacion.carrera_id == carrera_id,
                Asignacion.cohorte_id == cohorte_id_origen,
                Asignacion.desde <= today,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today),
            )
        )
        result = await self.session.execute(stmt)
        origen_vigentes = list(result.scalars().all())

        if not origen_vigentes:
            return []

        clonadas: list[Asignacion] = []
        for src in origen_vigentes:
            nueva = Asignacion(
                tenant_id=self.tenant_id,
                usuario_id=src.usuario_id,
                rol=src.rol,
                materia_id=materia_id,
                carrera_id=carrera_id,
                cohorte_id=cohorte_id_destino,
                comisiones=src.comisiones,
                responsable_id=src.responsable_id,
                desde=nueva_desde,
                # D3: If origen hasta=NULL, use nueva_hasta from request
                hasta=nueva_hasta,
            )
            self.session.add(nueva)
            clonadas.append(nueva)

        await self.session.flush()
        for c in clonadas:
            await self.session.refresh(c)
        return clonadas

    # ------------------------------------------------------------------
    # 1.1 Bulk vigency update (dry_run support)
    # ------------------------------------------------------------------

    async def actualizar_vigencia_equipo(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        nueva_desde: date,
        nueva_hasta: date | None,
        dry_run: bool = False,
    ) -> int:
        """
        Update desde/hasta for all assignments of a team (materia×carrera×cohorte).

        dry_run=True: returns the count of affected rows without modifying the DB.
        dry_run=False: applies the update and returns count.

        Multi-tenancy: always scoped to self.tenant_id.

        Args:
            materia_id: Context materia UUID.
            carrera_id: Context carrera UUID.
            cohorte_id: Context cohorte UUID.
            nueva_desde: New start date.
            nueva_hasta: New end date (None = open).
            dry_run: If True, do not apply changes.

        Returns:
            Number of assignments that would be (or were) affected.
        """
        # Count matching rows first (for dry_run or to return count)
        count_stmt = (
            select(Asignacion)
            .where(
                and_(
                    Asignacion.tenant_id == self.tenant_id,
                    Asignacion.materia_id == materia_id,
                    Asignacion.carrera_id == carrera_id,
                    Asignacion.cohorte_id == cohorte_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(count_stmt)
        affected = list(result.scalars().all())
        count = len(affected)

        if dry_run or count == 0:
            return count

        # Apply the update
        for asig in affected:
            asig.desde = nueva_desde
            asig.hasta = nueva_hasta

        await self.session.flush()
        return count
