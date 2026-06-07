from __future__ import annotations

import csv
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.guardias import GuardiaCreate, GuardiaResponse, GuardiaUpdate
from app.services.audit_service import AuditService, get_request_context
from app.services.guardia_service import GuardiaService

router = APIRouter(prefix="/api/v1/guardias", tags=["guardias"])


def _build_service(user: User, db: AsyncSession) -> GuardiaService:
    return GuardiaService(db, tenant_id=user.tenant_id)


@router.get(
    "",
    response_model=list[GuardiaResponse],
)
async def list_guardias(
    materia_id: UUID | None = None,
    carrera_id: UUID | None = None,
    cohorte_id: UUID | None = None,
    asignacion_id: UUID | None = None,
    estado: str | None = None,
    _: None = Depends(require_permission("guardias:registrar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GuardiaResponse]:
    """List guardias with optional filters."""
    service = _build_service(user, db)
    return await service.list(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        asignacion_id=asignacion_id,
        estado=estado,
    )  # type: ignore[return-value]


@router.post(
    "",
    response_model=GuardiaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_guardia(
    payload: GuardiaCreate,
    request: Request,
    _: None = Depends(require_permission("guardias:registrar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuardiaResponse:
    service = _build_service(user, db)
    guardia = await service.create(payload)

    audit = AuditService(db=db, tenant_id=user.tenant_id, **get_request_context(request))
    await audit.register(
        actor_id=user.id,
        accion=AuditAction.GUARDIA_REGISTRAR,
        materia_id=payload.materia_id,
        detalle={"guardia_id": str(guardia.id)},
    )

    return guardia  # type: ignore[return-value]


@router.patch(
    "/{guardia_id}",
    response_model=GuardiaResponse,
)
async def update_guardia(
    guardia_id: UUID,
    payload: GuardiaUpdate,
    _: None = Depends(require_permission("guardias:registrar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuardiaResponse:
    service = _build_service(user, db)
    return await service.update(guardia_id, payload)  # type: ignore[return-value]


@router.get(
    "/export",
    response_class=Response,
)
async def export_guardias_csv(
    materia_id: UUID | None = None,
    carrera_id: UUID | None = None,
    cohorte_id: UUID | None = None,
    estado: str | None = None,
    _: None = Depends(require_permission("guardias:registrar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export guardias as CSV file."""
    service = _build_service(user, db)
    guardias = await service.list(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        estado=estado,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Materia ID", "Carrera ID", "Cohorte ID",
        "Asignacion ID", "Día", "Horario", "Estado", "Comentarios",
    ])
    for g in guardias:
        writer.writerow([
            str(g.id), str(g.materia_id), str(g.carrera_id), str(g.cohorte_id),
            str(g.asignacion_id), g.dia, g.horario, g.estado, g.comentarios or "",
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=guardias.csv",
        },
    )
