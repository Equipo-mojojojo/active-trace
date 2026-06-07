from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.evaluaciones import (
    ConvocadoImport,
    ConvocadoResponse,
    EvaluacionCreate,
    EvaluacionResponse,
    EvaluacionUpdate,
)
from app.schemas.reservas import ReservaCreate, ReservaResponse
from app.schemas.resultados import ResultadoCreate, ResultadoResponse
from app.services.audit_service import AuditService, get_request_context
from app.services.convocado_service import ConvocadoService
from app.services.evaluacion_service import EvaluacionService
from app.services.metricas_service import MetricasService
from app.services.reserva_service import ReservaService
from app.services.resultado_service import ResultadoService

router = APIRouter(prefix="/api/v1/coloquios", tags=["coloquios"])


def _eval_service(user: User, db: AsyncSession) -> EvaluacionService:
    return EvaluacionService(db, tenant_id=user.tenant_id)


def _conv_service(user: User, db: AsyncSession) -> ConvocadoService:
    return ConvocadoService(db, tenant_id=user.tenant_id)


def _reserva_service(user: User, db: AsyncSession) -> ReservaService:
    return ReservaService(db, tenant_id=user.tenant_id)


def _resultado_service(user: User, db: AsyncSession) -> ResultadoService:
    return ResultadoService(db, tenant_id=user.tenant_id)


def _metricas_service(user: User, db: AsyncSession) -> MetricasService:
    return MetricasService(db, tenant_id=user.tenant_id)


# ── Métricas ──────────────────────────────────────────────────────────


@router.get("/metricas")
async def get_metricas_globales(
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = _metricas_service(user, db)
    return await service.globales()


# ── Convocatorias ─────────────────────────────────────────────────────


@router.get("", response_model=list[EvaluacionResponse])
async def list_evaluaciones(
    materia_id: UUID | None = None,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EvaluacionResponse]:
    service = _eval_service(user, db)
    return await service.list(materia_id=materia_id)  # type: ignore[return-value]


@router.post("", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluacion(
    payload: EvaluacionCreate,
    request: Request,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResponse:
    service = _eval_service(user, db)
    evaluacion = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.COLOQUIO_CREAR,
        materia_id=payload.materia_id,
        detalle={
            "evaluacion_id": str(evaluacion.id),
            "tipo": str(payload.tipo),
            "turnos": len(payload.turnos),
        },
    )

    return await service.get(evaluacion.id)  # type: ignore[return-value]


@router.get("/{evaluacion_id}", response_model=EvaluacionResponse)
async def get_evaluacion(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResponse:
    service = _eval_service(user, db)
    return await service.get(evaluacion_id)  # type: ignore[return-value]


@router.patch("/{evaluacion_id}", response_model=EvaluacionResponse)
async def update_evaluacion(
    evaluacion_id: UUID,
    payload: EvaluacionUpdate,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResponse:
    service = _eval_service(user, db)
    return await service.update(evaluacion_id, payload)  # type: ignore[return-value]


@router.post("/{evaluacion_id}/cerrar", response_model=EvaluacionResponse)
async def cerrar_evaluacion(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResponse:
    service = _eval_service(user, db)
    return await service.cerrar(evaluacion_id)  # type: ignore[return-value]


# ── Métricas por convocatoria ─────────────────────────────────────────


@router.get("/{evaluacion_id}/metricas")
async def get_metricas_convocatoria(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = _metricas_service(user, db)
    return await service.por_convocatoria(evaluacion_id)


# ── Convocados ────────────────────────────────────────────────────────


@router.get("/{evaluacion_id}/convocados", response_model=list[ConvocadoResponse])
async def list_convocados(
    evaluacion_id: UUID,
    q: str | None = None,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConvocadoResponse]:
    service = _conv_service(user, db)
    return await service.listar(evaluacion_id, q=q)  # type: ignore[return-value]


@router.post(
    "/{evaluacion_id}/convocados",
    status_code=status.HTTP_201_CREATED,
)
async def import_convocados(
    evaluacion_id: UUID,
    payload: ConvocadoImport,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = _conv_service(user, db)
    count = await service.importar(evaluacion_id, payload.alumno_ids)
    return {"importados": count}


@router.delete(
    "/{evaluacion_id}/convocados/{alumno_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_convocado(
    evaluacion_id: UUID,
    alumno_id: UUID,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = _conv_service(user, db)
    await service.remover(evaluacion_id, alumno_id)


# ── Reservas ──────────────────────────────────────────────────────────


@router.get("/{evaluacion_id}/reservas", response_model=list[ReservaResponse])
async def list_reservas(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReservaResponse]:
    service = _reserva_service(user, db)
    return await service.listar_por_evaluacion(evaluacion_id)  # type: ignore[return-value]


@router.post(
    "/{evaluacion_id}/reservas",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reservar_turno(
    evaluacion_id: UUID,
    payload: ReservaCreate,
    request: Request,
    _: None = Depends(require_permission("coloquios:reservar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReservaResponse:
    service = _reserva_service(user, db)
    reserva = await service.reservar(evaluacion_id, user.id, payload.turno_id)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.COLOQUIO_RESERVAR,
        materia_id=evaluacion_id,
        detalle={
            "reserva_id": str(reserva.id),
            "turno_id": str(payload.turno_id),
        },
    )

    return reserva  # type: ignore[return-value]


@router.get("/mis-reservas", response_model=list[ReservaResponse])
async def list_mis_reservas(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReservaResponse]:
    service = _reserva_service(user, db)
    return await service.listar_mis_reservas(user.id)  # type: ignore[return-value]


@router.delete(
    "/reservas/{reserva_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def cancelar_reserva(
    reserva_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = _reserva_service(user, db)
    await service.cancelar(reserva_id, user.id)


# ── Resultados ────────────────────────────────────────────────────────


@router.get("/{evaluacion_id}/resultados", response_model=list[ResultadoResponse])
async def list_resultados(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResultadoResponse]:
    service = _resultado_service(user, db)
    return await service.listar(evaluacion_id)  # type: ignore[return-value]


@router.post(
    "/{evaluacion_id}/resultados",
    response_model=ResultadoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_resultado(
    evaluacion_id: UUID,
    payload: ResultadoCreate,
    request: Request,
    _: None = Depends(require_permission("coloquios:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResultadoResponse:
    service = _resultado_service(user, db)
    resultado = await service.registrar_o_actualizar(
        evaluacion_id, payload.alumno_id, payload.nota_final
    )

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.COLOQUIO_RESULTADO,
        materia_id=evaluacion_id,
        detalle={
            "alumno_id": str(payload.alumno_id),
            "nota_final": payload.nota_final,
        },
    )

    return resultado  # type: ignore[return-value]


@router.get("/{evaluacion_id}/resultados/export", response_class=Response)
async def export_resultados_csv(
    evaluacion_id: UUID,
    _: None = Depends(require_permission("coloquios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = _resultado_service(user, db)
    csv_content = await service.export_csv(evaluacion_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=resultados_{evaluacion_id}.csv",
        },
    )
