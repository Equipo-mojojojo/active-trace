from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.factura import FacturaCreate, FacturaOut, FacturaUpdateEstado
from app.services.factura_service import (
    FacturaConflictError,
    FacturaNotFoundError,
    FacturaService,
)

router = APIRouter(prefix="/api/v1/facturas", tags=["facturas"])


def _service(user: User, db: AsyncSession) -> FacturaService:
    return FacturaService(db, tenant_id=user.tenant_id)


@router.get("", response_model=list[FacturaOut])
async def listar_facturas(
    estado: str | None = Query(None),
    periodo: str | None = Query(None),
    usuario_id: UUID | None = Query(None),
    _: None = Depends(require_permission("facturas:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FacturaOut]:
    service = _service(user, db)
    return await service.listar(estado=estado, periodo=periodo, usuario_id=usuario_id)  # type: ignore[return-value]


@router.post("", response_model=FacturaOut, status_code=status.HTTP_201_CREATED)
async def crear_factura(
    payload: FacturaCreate,
    _: None = Depends(require_permission("facturas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaOut:
    service = _service(user, db)
    try:
        result = await service.crear(**payload.model_dump())
    except FacturaConflictError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except FacturaNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result  # type: ignore[return-value]


@router.get("/{factura_id}", response_model=FacturaOut)
async def get_factura(
    factura_id: UUID,
    _: None = Depends(require_permission("facturas:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaOut:
    service = _service(user, db)
    facturas = await service.listar()
    row = next((f for f in facturas if f.id == factura_id), None)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return row  # type: ignore[return-value]


@router.patch("/{factura_id}/estado", response_model=FacturaOut)
async def cambiar_estado_factura(
    factura_id: UUID,
    payload: FacturaUpdateEstado,
    _: None = Depends(require_permission("facturas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaOut:
    service = _service(user, db)
    try:
        result = await service.cambiar_estado(factura_id, payload.estado)
    except FacturaNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result  # type: ignore[return-value]


@router.put("/{factura_id}/archivo", response_model=FacturaOut)
async def adjuntar_archivo(
    factura_id: UUID,
    archivo: UploadFile,
    _: None = Depends(require_permission("facturas:gestionar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacturaOut:
    import os
    import shutil

    upload_dir = "uploads/facturas"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{factura_id}_{archivo.filename}"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(archivo.file, f)

    service = _service(user, db)
    try:
        result = await service.adjuntar_archivo(factura_id, path)
    except FacturaNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result  # type: ignore[return-value]
