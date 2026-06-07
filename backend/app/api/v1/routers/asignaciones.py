"""
Asignaciones router for C-07: Assignment management endpoints.

Endpoints:
- GET /api/asignaciones — List own assignments with filters
- POST /api/asignaciones — Create assignment (equipos:asignar)
- GET /api/asignaciones/{id} — Get assignment details
- PATCH /api/asignaciones/{id} — Update assignment (equipos:asignar)
- DELETE /api/asignaciones/{id} — Soft delete assignment (equipos:asignar)
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.asignacion_schema import (
    AsignacionCreateRequest,
    AsignacionUpdateRequest,
    AsignacionResponseDTO,
)
from app.services.asignacion_service import (
    AsignacionService,
    AsignacionValidationError,
    AsignacionNotFoundError,
)

router = APIRouter(prefix="/api", tags=["asignaciones"])


@router.get("/asignaciones", response_model=list[AsignacionResponseDTO])
async def list_asignaciones(
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    estado_vigencia: str = Query(
        "vigente", pattern="^(vigente|vencida|futura|todas)$"
    ),
    materia_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AsignacionResponseDTO]:
    """
    List asignaciones for the current user.

    Filters:
    - estado_vigencia: vigente, vencida, futura, todas
    - materia_id: Optional materia filter

    Requires `equipos:asignar` permission.
    """
    service = AsignacionService(db)
    asignaciones = await service.list_all(
        usuario_id=user.id,
        tenant_id=user.tenant_id,
        estado_vigencia=estado_vigencia,
    )

    if materia_id:
        asignaciones = [a for a in asignaciones if a.materia_id == materia_id]

    return asignaciones[skip : skip + limit]


@router.post(
    "/asignaciones",
    response_model=AsignacionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_asignacion(
    payload: AsignacionCreateRequest,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponseDTO:
    """
    Create a new asignacion (role assignment).

    Requires `equipos:asignar` permission.
    """
    service = AsignacionService(db)
    try:
        return await service.create(payload, tenant_id=user.tenant_id)
    except AsignacionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/asignaciones/{asignacion_id}", response_model=AsignacionResponseDTO)
async def get_asignacion(
    asignacion_id: UUID,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponseDTO:
    """
    Get an asignacion by ID.

    Requires `equipos:asignar` permission.
    """
    service = AsignacionService(db)
    response = await service.get(asignacion_id, tenant_id=user.tenant_id)
    if not response:
        raise HTTPException(status_code=404, detail="Asignacion not found")
    return response


@router.patch(
    "/asignaciones/{asignacion_id}",
    response_model=AsignacionResponseDTO,
)
async def update_asignacion(
    asignacion_id: UUID,
    payload: AsignacionUpdateRequest,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionResponseDTO:
    """
    Update an asignacion (responsable_id, hasta only).

    Requires `equipos:asignar` permission.
    """
    service = AsignacionService(db)
    try:
        response = await service.update(asignacion_id, user.tenant_id, payload)
        if not response:
            raise HTTPException(status_code=404, detail="Asignacion not found")
        return response
    except AsignacionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/asignaciones/{asignacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_asignacion(
    asignacion_id: UUID,
    _: None = Depends(require_permission("equipos:asignar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete an asignacion.

    Requires `equipos:asignar` permission.
    """
    service = AsignacionService(db)
    try:
        await service.delete(asignacion_id, tenant_id=user.tenant_id)
    except AsignacionNotFoundError:
        raise HTTPException(status_code=404, detail="Asignacion not found")
