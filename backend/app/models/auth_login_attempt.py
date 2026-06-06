from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class AuthLoginAttempt(Base, BaseModelMixin):
    __tablename__ = "auth_login_attempt"

    email_lookup: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    was_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
