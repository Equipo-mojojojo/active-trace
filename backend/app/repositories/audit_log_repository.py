"""Repository for append-only audit log persistence.

Queries are intentionally limited: the audit log is a historical record,
not an operational table. All queries filter by tenant_id (enforced by
``TenantScopedRepository``), and only support listing with filters — no
update or delete methods are exposed.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select

from app.models.audit_log import AuditLog
from app.repositories.base import TenantScopedRepository


class AuditLogRepository(TenantScopedRepository[AuditLog]):
    """Repository for AuditLog entries.

    Append-only by design: does not expose ``soft_delete`` or any
    mutation method beyond ``create``. The DB trigger
    ``no_audit_update_delete`` enforces this at the database level.
    """

    def __init__(self, session, tenant_id: UUID | str):
        super().__init__(session, AuditLog, tenant_id)

    async def create_entry(
        self,
        *,
        actor_id: UUID,
        accion: str,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        detalle: dict | None = None,
        filas_afectadas: int | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and return a new audit log entry.

        The entry is flushed to DB (not committed) — the caller owns
        the transaction boundary.
        """
        entry = AuditLog(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            accion=accion,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    # ── Query helpers ───────────────────────────────────────────────

    @staticmethod
    def _apply_filters(
        statement: Select,
        *,
        tenant_id: UUID,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
        accion: str | None = None,
    ) -> Select:
        stmt = statement.where(AuditLog.tenant_id == tenant_id)
        if desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= hasta)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if materia_id is not None:
            stmt = stmt.where(AuditLog.materia_id == materia_id)
        if accion is not None:
            stmt = stmt.where(AuditLog.accion == accion)
        return stmt

    async def list_entries(
        self,
        *,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
        accion: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[AuditLog], int]:
        """List audit log entries with optional filters.

        Returns a tuple of ``(entries, total_count)``. Results are
        ordered by ``fecha_hora`` descending (most recent first).
        """
        base = self._apply_filters(
            select(AuditLog),
            tenant_id=self.tenant_id,
            desde=desde,
            hasta=hasta,
            actor_id=actor_id,
            materia_id=materia_id,
            accion=accion,
        )

        # Count query
        count_q = self._apply_filters(
            select(func.count(AuditLog.id)),
            tenant_id=self.tenant_id,
            desde=desde,
            hasta=hasta,
            actor_id=actor_id,
            materia_id=materia_id,
            accion=accion,
        )
        total_result = await self.session.execute(count_q)
        total = total_result.scalar_one()

        # Paginated list
        offset = (page - 1) * page_size
        stmt = base.order_by(AuditLog.fecha_hora.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        entries = result.scalars().all()
        return entries, total
