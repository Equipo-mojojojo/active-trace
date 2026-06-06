from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import new as hmac_new
from secrets import token_bytes
from secrets import token_urlsafe
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
import pyotp
from sqlalchemy.types import Text, TypeDecorator

from app.core.config import get_settings


ALGORITHM = "HS256"
NONCE_SIZE_BYTES = 12
password_hasher = PasswordHasher()


class EncryptionError(ValueError):
    pass


class TokenError(ValueError):
    pass


class EncryptedString(TypeDecorator[str]):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        del dialect

        if value is None:
            return None

        return encrypt_text(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        del dialect

        if value is None:
            return None

        return decrypt_text(value)


def _get_aesgcm() -> AESGCM:
    settings = get_settings()
    key = settings.ENCRYPTION_KEY.get_secret_value().encode("utf-8")
    return AESGCM(key)


def encrypt_text(plaintext: str) -> str:
    nonce = token_bytes(NONCE_SIZE_BYTES)
    ciphertext = _get_aesgcm().encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return urlsafe_b64encode(payload).decode("utf-8")


def decrypt_text(ciphertext: str) -> str:
    payload = urlsafe_b64decode(ciphertext.encode("utf-8"))
    nonce = payload[:NONCE_SIZE_BYTES]
    encrypted_bytes = payload[NONCE_SIZE_BYTES:]

    if not nonce or not encrypted_bytes:
        raise EncryptionError("Encrypted payload is invalid")

    plaintext = _get_aesgcm().decrypt(nonce, encrypted_bytes, None)
    return plaintext.decode("utf-8")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def build_email_lookup(email: str) -> str:
    settings = get_settings()
    normalized_email = normalize_email(email)
    secret_key = settings.SECRET_KEY.get_secret_value().encode("utf-8")
    return hmac_new(secret_key, normalized_email.encode("utf-8"), sha256).hexdigest()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def _encode_jwt(payload: dict[str, Any], expires_delta: timedelta) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + expires_delta
    encoded_payload = payload.copy()
    encoded_payload["exp"] = expires_at
    return jwt.encode(
        encoded_payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=ALGORITHM,
    )


def create_access_token(
    *,
    user_id: str,
    tenant_id: str,
    roles: list[str],
    es_impersonacion: bool = False,
    impersonado_id: str | None = None,
) -> str:
    """Create a JWT access token.

    When impersonating, the token carries extra claims:
    ``es_impersonacion: true`` and ``impersonado_id`` (the user being
    impersonated). The ``sub`` claim always identifies the real user
    (who logged in / who initiated the impersonation).
    """
    settings = get_settings()
    payload: dict[str, object] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "type": "access",
    }
    if es_impersonacion:
        payload["es_impersonacion"] = True
        if impersonado_id is not None:
            payload["impersonado_id"] = impersonado_id

    return _encode_jwt(
        payload,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_two_factor_challenge_token(
    *,
    user_id: str,
    tenant_id: str,
    roles: list[str],
) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "type": "two_factor",
    }
    return _encode_jwt(
        payload,
        timedelta(minutes=settings.TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES),
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[ALGORITHM],
        )
    except JWTError as exc:
        raise TokenError("Token is invalid") from exc

    if payload.get("type") != expected_type:
        raise TokenError("Token type is invalid")

    return payload


def create_opaque_token() -> str:
    return token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(secret: str, email: str) -> str:
    settings = get_settings()
    return pyotp.TOTP(secret).provisioning_uri(
        name=normalize_email(email),
        issuer_name=settings.TOTP_ISSUER,
    )


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
