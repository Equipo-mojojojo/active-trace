"""
PadronRepository: Persistence layer for VersionPadron and EntradaPadron.

Design decisions:
- All queries are tenant-scoped (TenantScopedRepository base).
- Activating a new version desactivates the previous one in the same
  logical operation (D1 in design.md).
- Queries never leak across tenant boundaries.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import TenantScopedRepository


class PadronRepository(TenantScopedRepository[VersionPadron]):
    """Repository for VersionPadron with tenant-scoped queries."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, VersionPadron, tenant_id)

    # ------------------------------------------------------------------
    # VersionPadron operations
    # ------------------------------------------------------------------

    async def obtener_version_activa(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> VersionPadron | None:
        """Return the single active version for (materia, cohorte), or None."""
        stmt = (
            self._statement()
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.activa.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def desactivar_version_activa(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> None:
        """Set activa=False on the current active version (without deleting it).

        Called within the same transaction as crear_version so the invariant
        (at most one activa=True per materia×cohorte) is always preserved.
        """
        stmt = (
            update(VersionPadron)
            .where(VersionPadron.tenant_id == self.tenant_id)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.activa.is_(True))
            .where(VersionPadron.deleted_at.is_(None))
            .values(activa=False)
        )
        await self.session.execute(stmt)

    async def crear_version(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        cargado_by: UUID | None = None,
        origen: str = "archivo",
    ) -> VersionPadron:
        """Create a new VersionPadron row (activa=True by default)."""
        return await self.create(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            activa=True,
            total_entradas=0,
            cargado_by=cargado_by,
            origen=origen,
        )

    async def actualizar_total_entradas(
        self,
        version_id: UUID,
        total: int,
    ) -> None:
        """Update total_entradas counter after bulk insert."""
        stmt = (
            update(VersionPadron)
            .where(VersionPadron.id == version_id)
            .values(total_entradas=total)
        )
        await self.session.execute(stmt)

    async def listar_versiones(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        include_deleted: bool = False,
    ) -> list[VersionPadron]:
        """List all versions for (materia, cohorte), ordered by created_at DESC."""
        stmt = (
            self._statement(include_deleted=include_deleted)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .order_by(desc(VersionPadron.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def listar_versiones_activas_por_materia(
        self,
        materia_id: UUID,
        include_deleted: bool = False,
    ) -> list[VersionPadron]:
        """List active versions for a materia across all cohortes in the tenant."""
        stmt = (
            self._statement(include_deleted=include_deleted)
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.activa.is_(True))
            .order_by(desc(VersionPadron.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_version(self, version_id: UUID) -> VersionPadron | None:
        """Soft-delete a VersionPadron (sets deleted_at and activa=False)."""
        version = await self.get_by_id(version_id)
        if version is None:
            return None
        version.mark_deleted()
        version.activa = False
        await self.session.flush()
        await self.session.refresh(version)
        return version

    # ------------------------------------------------------------------
    # EntradaPadron bulk operations
    # ------------------------------------------------------------------

    async def crear_entradas_bulk(
        self,
        version_id: UUID,
        entradas: list[dict],
    ) -> int:
        """Insert multiple EntradaPadron rows in bulk.

        entradas: list of dicts with keys:
          nombre, apellidos, email (optional), comision (optional),
          regional (optional), usuario_id (optional).

        Returns the count of rows inserted.
        """
        if not entradas:
            return 0

        rows = []
        for row in entradas:
            entrada = EntradaPadron(
                tenant_id=self.tenant_id,
                version_id=version_id,
                nombre=row.get("nombre", ""),
                apellidos=row.get("apellidos", ""),
                email=row.get("email"),
                comision=row.get("comision"),
                regional=row.get("regional"),
                usuario_id=row.get("usuario_id"),
            )
            rows.append(entrada)

        self.session.add_all(rows)
        await self.session.flush()
        return len(rows)

    async def listar_entradas(
        self,
        version_id: UUID,
        include_deleted: bool = False,
    ) -> list[EntradaPadron]:
        """List all EntradaPadron rows for a version."""
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self.tenant_id,
            EntradaPadron.version_id == version_id,
        )
        if not include_deleted:
            stmt = stmt.where(EntradaPadron.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
