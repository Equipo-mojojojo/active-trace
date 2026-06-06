from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.metricas_auditoria_repository import MetricasAuditoriaRepository
from app.schemas.metricas_auditoria import AUDIT_MAX_LIMIT


def aplicar_limite(limite: int | None, max_limit: int = AUDIT_MAX_LIMIT) -> int:
    """Pure function: apply cap to requested limit."""
    if not limite or limite <= 0:
        return max_limit
    return min(limite, max_limit)


def resolver_actor_scope(perms: set[str], user_id: str) -> str | None:
    """Pure function: resolve actor_id filter based on user permissions.

    Returns None for unrestricted access (auditoria:ver),
    user_id string for self-scoped access (auditoria:ver:propio only).
    """
    if "auditoria:ver" in perms:
        return None
    if "auditoria:ver:propio" in perms:
        return user_id
    return None


class MetricasAuditoriaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self._repo = MetricasAuditoriaRepository(session, tenant_id)

    async def acciones_por_dia(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
    ) -> list[dict]:
        return await self._repo.acciones_por_dia(
            desde=desde, hasta=hasta, actor_id=actor_id, materia_id=materia_id
        )

    async def estado_comunicaciones(
        self,
        materia_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> list[dict]:
        return await self._repo.estado_comunicaciones(
            materia_id=materia_id, actor_id=actor_id
        )

    async def interacciones_por_docente_materia(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: UUID | None = None,
    ) -> list[dict]:
        return await self._repo.interacciones_por_docente_materia(
            desde=desde, hasta=hasta, actor_id=actor_id
        )

    async def ultimas_acciones(
        self,
        limite: int | None = None,
        materia_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> list[AuditLog]:
        cap = aplicar_limite(limite)
        return await self._repo.ultimas_acciones(
            limite=cap, materia_id=materia_id, actor_id=actor_id
        )
