from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)

    model_config = ConfigDict(extra="forbid")


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class LogoutRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class ForgotPasswordRequest(BaseModel):
    email: str

    model_config = ConfigDict(extra="forbid")


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    model_config = ConfigDict(extra="forbid")


class TwoFactorEnrollmentResponse(BaseModel):
    secret: str
    provisioning_uri: str

    model_config = ConfigDict(extra="forbid")


class TwoFactorCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)

    model_config = ConfigDict(extra="forbid")


class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=6)

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    requires_two_factor: bool = False
    challenge_token: str | None = None

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(extra="forbid")


class CurrentUserResponse(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str]
    email: str

    model_config = ConfigDict(extra="forbid")
