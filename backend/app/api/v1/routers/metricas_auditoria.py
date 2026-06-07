from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import get_effective_permissions
from app.models.user import User
from app.schemas.metricas_auditoria import (
    AccionPorDiaOut,
    EstadoComunicacionPorDocenteOut,
    InteraccionPorDocenteMateriaOut,
    UltimaAccionOut,
)
from app.services.metricas_auditoria_service import (
    MetricasAuditoriaService,
    resolver_actor_scope,
)

router = APIRouter(prefix="/api/v1/auditoria/metricas", tags=["auditoria-metricas"])

_AUDITORIA_PERMS = {"auditoria:ver", "auditoria:ver:propio"}


async def _require_auditoria(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, set[str]]:
    """Dependency: requires auditoria:ver OR auditoria:ver:propio."""
    perms = await get_effective_permissions(user_id=user.id, tenant_id=user.tenant_id, db=db)
    if not perms & _AUDITORIA_PERMS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso de auditoría")
    return user, perms


def _service(user: User, db: AsyncSession) -> MetricasAuditoriaService:
    return MetricasAuditoriaService(db, tenant_id=user.tenant_id)


def _actor_filter(perms: set[str], user: User, actor_id: UUID | None) -> UUID | None:
    scope = resolver_actor_scope(perms, str(user.id))
    if scope is not None:
        return user.id
    return actor_id


@router.get("/acciones-por-dia", response_model=list[AccionPorDiaOut])
async def acciones_por_dia(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    actor_id: UUID | None = Query(None),
    materia_id: UUID | None = Query(None),
    auth: tuple = Depends(_require_auditoria),
    db: AsyncSession = Depends(get_db),
) -> list[AccionPorDiaOut]:
    user, perms = auth
    actor = _actor_filter(perms, user, actor_id)
    service = _service(user, db)
    result = await service.acciones_por_dia(
        desde=desde, hasta=hasta, actor_id=actor, materia_id=materia_id
    )
    return [AccionPorDiaOut(**r) for r in result]


@router.get("/estado-comunicaciones", response_model=list[EstadoComunicacionPorDocenteOut])
async def estado_comunicaciones(
    materia_id: UUID | None = Query(None),
    actor_id: UUID | None = Query(None),
    auth: tuple = Depends(_require_auditoria),
    db: AsyncSession = Depends(get_db),
) -> list[EstadoComunicacionPorDocenteOut]:
    user, perms = auth
    actor = _actor_filter(perms, user, actor_id)
    service = _service(user, db)
    result = await service.estado_comunicaciones(materia_id=materia_id, actor_id=actor)
    return [EstadoComunicacionPorDocenteOut(**r) for r in result]


@router.get("/interacciones", response_model=list[InteraccionPorDocenteMateriaOut])
async def interacciones(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    actor_id: UUID | None = Query(None),
    auth: tuple = Depends(_require_auditoria),
    db: AsyncSession = Depends(get_db),
) -> list[InteraccionPorDocenteMateriaOut]:
    user, perms = auth
    actor = _actor_filter(perms, user, actor_id)
    service = _service(user, db)
    result = await service.interacciones_por_docente_materia(
        desde=desde, hasta=hasta, actor_id=actor
    )
    return [InteraccionPorDocenteMateriaOut(**r) for r in result]


@router.get("/ultimas-acciones", response_model=list[UltimaAccionOut])
async def ultimas_acciones(
    limite: int | None = Query(None, ge=1),
    materia_id: UUID | None = Query(None),
    actor_id: UUID | None = Query(None),
    auth: tuple = Depends(_require_auditoria),
    db: AsyncSession = Depends(get_db),
) -> list[UltimaAccionOut]:
    user, perms = auth
    actor = _actor_filter(perms, user, actor_id)
    service = _service(user, db)
    entries = await service.ultimas_acciones(
        limite=limite, materia_id=materia_id, actor_id=actor
    )
    return entries  # type: ignore[return-value]
