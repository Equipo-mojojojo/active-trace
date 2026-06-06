from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin


class PasswordResetToken(Base, TenantScopedModelMixin):
    __tablename__ = "password_reset_token"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("user_account.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    token_value: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
