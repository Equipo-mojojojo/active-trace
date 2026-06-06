from __future__ import annotations

from sqlalchemy import Boolean, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin


class User(Base, TenantScopedModelMixin):
    __tablename__ = "user_account"
    __table_args__ = (
        UniqueConstraint("email_lookup", name="uq_user_account_email_lookup"),
    )

    email: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    email_lookup: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    totp_secret: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
