"""Impersonation endpoints — iniciar / finalizar.

Initiating impersonation requires ``impersonacion:usar`` permission.
Finalizing is allowed for anyone with a valid impersonation token
(since only authorised users could have obtained one).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.core.security import create_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.audit import (
    ImpersonacionTokenResponse,
    IniciarImpersonacionRequest,
)
from app.services.audit_service import AuditService, get_request_context

router = APIRouter(prefix="/api/admin", tags=["admin-impersonacion"])


@router.post(
    "/impersonacion/iniciar",
    response_model=ImpersonacionTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def iniciar_impersonacion(
    payload: IniciarImpersonacionRequest,
    request: Request,
    _: None = Depends(require_permission("impersonacion:usar")),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonacionTokenResponse:
    """Start an impersonation session.

    Issues a new JWT access token with ``es_impersonacion: true`` and
    ``impersonado_id`` claims. The ``sub`` claim remains the real
    user's ID for audit attribution.
    """
    # Validate target user exists and is in the same tenant
    repository = UserRepository(db)
    target = await repository.get_authenticated_user(
        user_id=str(payload.usuario_id),
        tenant_id=str(user.tenant_id),
    )
    if target is None or not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o inactivo",
        )

    # Issue impersonation token
    impersonation_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        roles=list(user.roles),
        es_impersonacion=True,
        impersonado_id=str(target.id),
    )

    # Register in audit log
    context = get_request_context(request)
    audit = AuditService(
        db=db,
        tenant_id=user.tenant_id,
        **context,
    )
    await audit.register(
        actor_id=user.id,
        impersonado_id=target.id,
        accion=AuditAction.IMPERSONACION_INICIAR,
    )
    await db.commit()

    return ImpersonacionTokenResponse(access_token=impersonation_token)


@router.post(
    "/impersonacion/finalizar",
    response_model=ImpersonacionTokenResponse,
)
async def finalizar_impersonacion(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonacionTokenResponse:
    """End an impersonation session.

    Issues a fresh normal JWT access token for the real user.
    Only works if the current request carries a valid impersonation
    token (``es_impersonacion: true``).
    """
    # Retrieve the real actor's identity set by get_current_user
    real_user_id = getattr(request.state, "actor_real_id", None)
    real_tenant_id = getattr(request.state, "actor_real_tenant_id", None)

    if real_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay una sesión de impersonación activa",
        )

    # Load the real user to create a fresh token
    repository = UserRepository(db)
    real_user = await repository.get_authenticated_user(
        user_id=str(real_user_id),
        tenant_id=str(real_tenant_id),
    )
    if real_user is None or not real_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario real ya no está activo",
        )

    normal_token = create_access_token(
        user_id=str(real_user.id),
        tenant_id=str(real_user.tenant_id),
        roles=list(real_user.roles),
    )

    # Register in audit log
    context = get_request_context(request)
    audit = AuditService(
        db=db,
        tenant_id=real_tenant_id,
        **context,
    )
    await audit.register(
        actor_id=real_user.id,
        impersonado_id=user.id,
        accion=AuditAction.IMPERSONACION_FINALIZAR,
    )
    await db.commit()

    return ImpersonacionTokenResponse(access_token=normal_token)
