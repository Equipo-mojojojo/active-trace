from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.liquidacion import (
    CerrarLiquidacionOut,
    LiquidacionSegmentadaOut,
)
from app.schemas.salario_base import SalarioBaseCreate, SalarioBaseOut, SalarioBaseUpdate
from app.schemas.salario_plus import SalarioPlusCreate, SalarioPlusOut, SalarioPlusUpdate
from app.services.audit_service import AuditService, get_request_context
from app.services.grilla_salarial_service import GrillaSalarialConflictError, GrillaSalarialService
from app.services.liquidacion_service import LiquidacionConflictError, LiquidacionService
from fastapi import Request

router = APIRouter(prefix="/api/v1/liquidaciones", tags=["liquidaciones"])


def _liquidacion_service(user: User, db: AsyncSession) -> LiquidacionService:
    return LiquidacionService(db, tenant_id=user.tenant_id)


def _grilla_service(user: User, db: AsyncSession) -> GrillaSalarialService:
    return GrillaSalarialService(db, tenant_id=user.tenant_id)


# ---------------------------------------------------------------------------
# Liquidaciones
# ---------------------------------------------------------------------------


@router.get("", response_model=LiquidacionSegmentadaOut)
async def listar_liquidaciones(
    periodo: str = Query(..., description="Período AAAA-MM"),
    _: None = Depends(require_permission("liquidaciones:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LiquidacionSegmentadaOut:
    service = _liquidacion_service(user, db)
    result = await service.obtener_segmentada(periodo)
    return LiquidacionSegmentadaOut(
        general=result.general,
        nexo=result.nexo,
        facturantes=result.facturantes,
        total_sin_factura=result.total_sin_factura,
        total_con_factura=result.total_con_factura,
    )


@router.post("/{periodo}/cerrar", response_model=CerrarLiquidacionOut)
async def cerrar_liquidacion(
    periodo: str,
    request: Request,
    _: None = Depends(require_permission("liquidaciones:cerrar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CerrarLiquidacionOut:
    audit = AuditService(db, **get_request_context(request))
    service = LiquidacionService(db, tenant_id=user.tenant_id, audit=audit)
    try:
        liquidaciones = await service.cerrar_periodo(periodo, actor_id=user.id, actor_tenant_id=user.tenant_id)
    except LiquidacionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return CerrarLiquidacionOut(
        periodo=periodo,
        liquidaciones_cerradas=len(liquidaciones),
    )


@router.get("/historial", response_model=list)
async def historial_liquidaciones(
    _: None = Depends(require_permission("liquidaciones:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    service = _liquidacion_service(user, db)
    return await service.historial()


# ---------------------------------------------------------------------------
# Grilla salarial — base
# ---------------------------------------------------------------------------


@router.get("/salarios/base", response_model=list[SalarioBaseOut])
async def listar_salario_base(
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SalarioBaseOut]:
    service = _grilla_service(user, db)
    return await service.listar_base()  # type: ignore[return-value]


@router.post(
    "/salarios/base",
    response_model=SalarioBaseOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_salario_base(
    payload: SalarioBaseCreate,
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioBaseOut:
    service = _grilla_service(user, db)
    try:
        result = await service.crear_base(**payload.model_dump())
    except GrillaSalarialConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return result  # type: ignore[return-value]


@router.put("/salarios/base/{record_id}", response_model=SalarioBaseOut)
async def actualizar_salario_base(
    record_id: UUID,
    payload: SalarioBaseUpdate,
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioBaseOut:
    service = _grilla_service(user, db)
    try:
        result = await service.actualizar_base(record_id, **payload.model_dump(exclude_none=True))
    except GrillaSalarialConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Grilla salarial — plus
# ---------------------------------------------------------------------------


@router.get("/salarios/plus", response_model=list[SalarioPlusOut])
async def listar_salario_plus(
    grupo: str | None = Query(None),
    rol: str | None = Query(None),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SalarioPlusOut]:
    service = _grilla_service(user, db)
    return await service.listar_plus(grupo=grupo, rol=rol)  # type: ignore[return-value]


@router.post(
    "/salarios/plus",
    response_model=SalarioPlusOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_salario_plus(
    payload: SalarioPlusCreate,
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalarioPlusOut:
    service = _grilla_service(user, db)
    try:
        result = await service.crear_plus(**payload.model_dump())
    except GrillaSalarialConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return result  # type: ignore[return-value]
