"""
Analisis router for C-11: atrasados, ranking, reporte, notas finales, monitor, export.

Endpoints:
  GET  /api/v1/analisis/atrasados              — F2.2 (atrasados:ver)
  GET  /api/v1/analisis/ranking                — F2.3 (atrasados:ver)
  GET  /api/v1/analisis/reporte                — F2.4 (atrasados:ver)
  GET  /api/v1/analisis/notas-finales          — F2.5 (atrasados:ver)
  GET  /api/v1/analisis/monitor                — F2.7–F2.9 (atrasados:ver)
  GET  /api/v1/analisis/export/sin-corregir    — F2.6 (atrasados:ver)

Architecture:
  - Identity always from JWT, never from request params.
  - Business logic in AnalisisService.
  - Queries in AnalisisRepository.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.analisis import (
    AtrasadosResponse,
    MonitorResponse,
    NotasFinalResponse,
    RankingResponse,
    ReporteRapidoResponse,
)
from app.services.analisis_service import AnalisisService

router = APIRouter(prefix="/api/v1/analisis", tags=["analisis"])


def _svc(user: User, db: AsyncSession) -> AnalisisService:
    return AnalisisService(session=db, tenant_id=user.tenant_id)


# ---------------------------------------------------------------------------
# GET /atrasados — F2.2
# ---------------------------------------------------------------------------


@router.get("/atrasados", response_model=AtrasadosResponse, status_code=status.HTTP_200_OK)
async def get_atrasados(
    materia_id: UUID = Query(...),
    cohorte_id: Optional[UUID] = Query(default=None),
    comision: Optional[str] = Query(default=None),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    return await svc.obtener_atrasados(
        materia_id=materia_id, cohorte_id=cohorte_id, comision=comision
    )


# ---------------------------------------------------------------------------
# GET /ranking — F2.3
# ---------------------------------------------------------------------------


@router.get("/ranking", response_model=RankingResponse, status_code=status.HTTP_200_OK)
async def get_ranking(
    materia_id: UUID = Query(...),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    return await svc.obtener_ranking(materia_id=materia_id)


# ---------------------------------------------------------------------------
# GET /reporte — F2.4
# ---------------------------------------------------------------------------


@router.get("/reporte", response_model=ReporteRapidoResponse, status_code=status.HTTP_200_OK)
async def get_reporte(
    materia_id: UUID = Query(...),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    return await svc.obtener_reporte(materia_id=materia_id)


# ---------------------------------------------------------------------------
# GET /notas-finales — F2.5
# ---------------------------------------------------------------------------


@router.get(
    "/notas-finales", response_model=NotasFinalResponse, status_code=status.HTTP_200_OK
)
async def get_notas_finales(
    materia_id: UUID = Query(...),
    actividades: list[str] = Query(default=[]),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    return await svc.obtener_notas_finales(
        materia_id=materia_id, actividades_seleccionadas=actividades
    )


# ---------------------------------------------------------------------------
# GET /monitor — F2.7–F2.9
# ---------------------------------------------------------------------------


@router.get("/monitor", response_model=MonitorResponse, status_code=status.HTTP_200_OK)
async def get_monitor(
    materia_id: Optional[UUID] = Query(default=None),
    comision: Optional[str] = Query(default=None),
    regional: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    min_aprobadas: Optional[int] = Query(default=None, ge=0),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    return await svc.obtener_monitor(
        actor=user,
        materia_id=materia_id,
        comision=comision,
        regional=regional,
        q=q,
        min_aprobadas=min_aprobadas,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /export/sin-corregir — F2.6
# ---------------------------------------------------------------------------


@router.get("/export/sin-corregir", status_code=status.HTTP_200_OK)
async def export_sin_corregir(
    materia_id: UUID = Query(...),
    _: None = Depends(require_permission("atrasados:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(user, db)
    csv_content = await svc.export_sin_corregir_csv(materia_id=materia_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=\"sin_corregir_{materia_id}.csv\""
        },
    )
