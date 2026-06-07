from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.core.security import TokenError, decode_token
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Resolve the current authenticated user from the JWT.

    Under impersonation, returns the impersonated user (the one being
    acted *as*) while preserving the real actor's identity in
    ``request.state.actor_real_id`` and
    ``request.state.actor_real_tenant_id``.

    The ``request.state`` fields set here are consumed by
    ``AuditService`` to correctly attribute actions.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise credentials_exception from exc

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", [])

    if user_id is None or tenant_id is None or not isinstance(roles, list):
        raise credentials_exception

    # ── Impersonation branch ───────────────────────────────────────
    if payload.get("es_impersonacion") and payload.get("impersonado_id"):
        # The real actor is in `sub`; save it for AuditService
        request.state.actor_real_id = user_id
        request.state.actor_real_tenant_id = tenant_id

        # Load the impersonated user for permission / identity checks
        impersonado_id = payload["impersonado_id"]
        repository = UserRepository(db)
        impersonated = await repository.get_authenticated_user(
            user_id=impersonado_id,
            tenant_id=tenant_id,
        )
        if impersonated is None or not impersonated.is_active:
            raise credentials_exception

        return impersonated

    # ── Normal authentication flow ─────────────────────────────────
    repository = UserRepository(db)
    user = await repository.get_authenticated_user(user_id=user_id, tenant_id=tenant_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user
