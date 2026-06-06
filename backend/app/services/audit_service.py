"""Audit service — register actions in the append-only audit log.

Usage::

    from app.core.audit_constants import AuditAction
    from app.services.audit_service import AuditService

    # Inside an endpoint:
    audit = AuditService(db=db, tenant_id=user.tenant_id,
                         ip=request.state.ip,
                         user_agent=request.state.user_agent)
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.CALIFICACIONES_IMPORTAR,
        materia_id=materia.id,
        filas_afectadas=42,
    )
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.repositories.audit_log_repository import AuditLogRepository


class AuditActionError(ValueError):
    """Raised when an invalid action code is passed to the service."""


class AuditService:
    """Service for registering actions in the append-only audit log.

    Thread-safe within a single request context. Does NOT expose any
    update or delete methods — the DB trigger enforces append-only at
    the database level as a second line of defence.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: UUID | str,
        ip: str | None = None,
        user_agent: str | None = None,
    ):
        self._repository = AuditLogRepository(db, tenant_id)
        self._ip = ip
        self._user_agent = user_agent

    async def register(
        self,
        *,
        actor_id: UUID,
        accion: str | AuditAction,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        detalle: dict | None = None,
        filas_afectadas: int | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Register an action in the audit log.

        Args:
            actor_id: ID of the user who performed the action.
            accion: Action code — must be a valid ``AuditAction`` value.
            impersonado_id: ID of the impersonated user, if any.
            materia_id: ID of the related subject instance, if any.
            detalle: Optional JSON-serialisable detail payload.
            filas_afectadas: Number of affected rows / records.
            ip: Override for auto-detected IP (from middleware).
            user_agent: Override for auto-detected User-Agent.

        Raises:
            AuditActionError: If ``accion`` is not a valid ``AuditAction``.
        """
        self._validate_action(accion)

        await self._repository.create_entry(
            actor_id=actor_id,
            accion=str(accion),
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip or self._ip,
            user_agent=user_agent or self._user_agent,
        )

    @staticmethod
    def _validate_action(accion: str | AuditAction) -> None:
        """Check that ``accion`` is a known ``AuditAction`` value.

        Raises ``AuditActionError`` for invalid codes — this is a
        programming error, not a runtime data variation.
        """
        if isinstance(accion, AuditAction):
            return

        try:
            AuditAction(accion)
        except ValueError as exc:
            raise AuditActionError(
                f"'{accion}' is not a valid audit action. "
                f"Use one of: {', '.join(sorted(AuditAction))}"
            ) from exc


# ── Helper: extract request context ────────────────────────────────


def get_request_context(request: Request) -> dict[str, str | None]:
    """Extract IP and User-Agent from ``request.state`` (set by AuditMiddleware).

    Returns a dict with ``ip`` and ``user_agent`` keys. When the
    middleware hasn't run, both default to ``None``.

    Usage::

        context = get_request_context(request)
        audit = AuditService(db=db, tenant_id=user.tenant_id, **context)
    """
    return {
        "ip": getattr(request.state, "ip", None),
        "user_agent": getattr(request.state, "user_agent", None),
    }
