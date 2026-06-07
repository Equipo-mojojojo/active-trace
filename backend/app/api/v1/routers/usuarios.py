"""
Usuarios router for C-07: User management endpoints.

Endpoints:
- POST /api/admin/usuarios — Create usuario (ADMIN only)
- GET /api/admin/usuarios — List usuarios (ADMIN only)
- GET /api/admin/usuarios/{id} — Get usuario (ADMIN only)
- PATCH /api/admin/usuarios/{id} — Update usuario (ADMIN only)
- DELETE /api/admin/usuarios/{id} — Soft delete usuario (ADMIN only)

All endpoints return UsuarioResponseDTO (no PII).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.usuario_schema import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    UsuarioResponseDTO,
)
from app.services.usuario_service import (
    UsuarioService,
    UsuarioAlreadyExistsError,
    UsuarioNotFoundError,
)

router = APIRouter(prefix="/api/admin", tags=["usuarios"])


@router.post(
    "/usuarios",
    response_model=UsuarioResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_usuario(
    payload: UsuarioCreateRequest,
    _: None = Depends(require_permission("usuarios:crear")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponseDTO:
    """
    Create a new usuario.

    Requires `usuarios:crear` permission.
    """
    service = UsuarioService(db)
    try:
        return await service.create(payload, tenant_id=user.tenant_id)
    except UsuarioAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/usuarios", response_model=list[UsuarioResponseDTO])
async def list_usuarios(
    _: None = Depends(require_permission("usuarios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[UsuarioResponseDTO]:
    """
    List all usuarios in tenant.

    Requires `usuarios:ver` permission.
    """
    service = UsuarioService(db)
    return await service.list(tenant_id=user.tenant_id, skip=skip, limit=limit)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponseDTO)
async def get_usuario(
    usuario_id: UUID,
    _: None = Depends(require_permission("usuarios:ver")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponseDTO:
    """
    Get a usuario by ID.

    Requires `usuarios:ver` permission.
    """
    service = UsuarioService(db)
    response = await service.get(usuario_id, tenant_id=user.tenant_id)
    if not response:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return response


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponseDTO)
async def update_usuario(
    usuario_id: UUID,
    payload: UsuarioUpdateRequest,
    _: None = Depends(require_permission("usuarios:modificar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponseDTO:
    """
    Update a usuario (nombre, apellidos only).

    Requires `usuarios:modificar` permission.
    """
    service = UsuarioService(db)
    response = await service.update(usuario_id, user.tenant_id, payload)
    if not response:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return response


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: UUID,
    _: None = Depends(require_permission("usuarios:eliminar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete a usuario.

    Requires `usuarios:eliminar` permission.
    """
    service = UsuarioService(db)
    try:
        await service.delete(usuario_id, tenant_id=user.tenant_id)
    except UsuarioNotFoundError:
        raise HTTPException(status_code=404, detail="Usuario not found")
