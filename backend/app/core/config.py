from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "activia-trace"
    DATABASE_URL: str
    SECRET_KEY: SecretStr
    ENCRYPTION_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES: int = 5
    TOTP_ISSUER: str = "activia-trace"
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    LOG_LEVEL: str = "INFO"
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "activia-trace-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")
        return value

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) != 32:
            raise ValueError("ENCRYPTION_KEY must contain exactly 32 characters")
        return value

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer")
        return value

    @field_validator(
        "REFRESH_TOKEN_EXPIRE_MINUTES",
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
        "TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES",
        "LOGIN_RATE_LIMIT_MAX_ATTEMPTS",
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS",
    )
    @classmethod
    def validate_positive_integers(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Authentication timing values must be positive integers")
        return value

    @field_validator("TOTP_ISSUER")
    @classmethod
    def validate_totp_issuer(cls, value: str) -> str:
        sanitized_value = value.strip()
        if not sanitized_value:
            raise ValueError("TOTP_ISSUER must not be blank")
        return sanitized_value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
