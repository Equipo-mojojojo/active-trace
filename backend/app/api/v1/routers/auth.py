from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import get_effective_permissions
from app.models.tenant import Tenant
from app.repositories.auth_repository import AuthRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    AuthTenantResponse,
    AuthUserResponse,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    TwoFactorCodeRequest,
    TwoFactorEnrollmentResponse,
    TwoFactorVerifyRequest,
)
from app.services.auth_service import AuthError, AuthService, RateLimitExceededError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def build_auth_service(db: AsyncSession) -> AuthService:
    return AuthService(UserRepository(db), AuthRepository(db))


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


async def _build_auth_response(
    result,
    db: AsyncSession,
    response: Response | None = None,
) -> AuthResponse:
    """Build enriched AuthResponse from AuthenticationResult and optionally set cookie."""
    settings = get_settings()

    # When 2FA challenge is required, return minimal response
    if result.requires_two_factor:
        return AuthResponse(
            requires_two_factor=True,
            requires_2fa=True,
            challenge_token=result.challenge_token,
            session_token=result.challenge_token,
            access_token=None,
        )

    # Fetch tenant for name
    tenant_row = await db.execute(
        select(Tenant).where(Tenant.id == UUID(result.user_tenant_id))
    )
    tenant = tenant_row.scalar_one_or_none()

    # Resolve permissions
    perms = await get_effective_permissions(
        user_id=result.user_id,
        tenant_id=result.user_tenant_id,
        db=db,
    )

    # Set httpOnly refresh-token cookie when a Response object is provided
    if response is not None and result.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=result.refresh_token,
            httponly=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            path="/api/v1/auth",
        )

    return AuthResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type="bearer",
        expires_in=result.expires_in,
        requires_two_factor=False,
        requires_2fa=False,
        user=AuthUserResponse(
            id=result.user_id,
            nombre=result.user_full_name,
            email=result.user_email,
        ),
        permissions=sorted(perms),
        roles=result.user_roles,
        tenant=AuthTenantResponse(
            id=result.user_tenant_id,
            nombre=tenant.name if tenant else "Unknown",
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    auth_service = build_auth_service(db)

    try:
        result = await auth_service.login(
            email=payload.email,
            password=payload.password,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return await _build_auth_response(result, db, response)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    auth_service = build_auth_service(db)

    # Body takes priority so existing tests keep working; cookie is the frontend path
    token = (payload.refresh_token if payload else None) or request.cookies.get(
        "refresh_token"
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        result = await auth_service.refresh(refresh_token=token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return await _build_auth_response(result, db, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest | None = Body(default=None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    auth_service = build_auth_service(db)

    token = (payload.refresh_token if payload else None) or request.cookies.get(
        "refresh_token"
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        await auth_service.logout(current_user=current_user, refresh_token=token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = build_auth_service(db)
    await auth_service.forgot_password(email=payload.email)
    return MessageResponse(
        message="If the account exists, recovery instructions have been issued"
    )


@router.post("/reset", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = build_auth_service(db)

    try:
        await auth_service.reset_password(
            token=payload.token, new_password=payload.new_password
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return MessageResponse(message="Password updated successfully")


@router.post("/2fa/enroll", response_model=TwoFactorEnrollmentResponse)
async def enroll_two_factor(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorEnrollmentResponse:
    auth_service = build_auth_service(db)
    secret, provisioning_uri = await auth_service.begin_two_factor_enrollment(
        current_user=current_user
    )
    return TwoFactorEnrollmentResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post("/2fa/enable", response_model=MessageResponse)
async def enable_two_factor(
    payload: TwoFactorCodeRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    auth_service = build_auth_service(db)

    try:
        await auth_service.enable_two_factor(
            current_user=current_user, code=payload.code
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return MessageResponse(message="Two-factor authentication enabled")


@router.post("/2fa/verify", response_model=AuthResponse)
async def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    auth_service = build_auth_service(db)

    try:
        result = await auth_service.verify_two_factor_login(
            challenge_token=payload.challenge_token,
            code=payload.code,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return await _build_auth_response(result, db, response)


@router.get("/me", response_model=CurrentUserResponse)
async def read_current_user(
    current_user=Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        roles=list(current_user.roles),
        email=current_user.email,
    )
