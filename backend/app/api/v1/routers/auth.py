from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.repositories.auth_repository import AuthRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
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

router = APIRouter(prefix="/api/auth", tags=["auth"])


def build_auth_service(db: AsyncSession) -> AuthService:
    return AuthService(UserRepository(db), AuthRepository(db))


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
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

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        requires_two_factor=result.requires_two_factor,
        challenge_token=result.challenge_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = build_auth_service(db)

    try:
        result = await auth_service.refresh(refresh_token=payload.refresh_token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    auth_service = build_auth_service(db)

    try:
        await auth_service.logout(
            current_user=current_user, refresh_token=payload.refresh_token
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

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


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
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

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
    )


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
