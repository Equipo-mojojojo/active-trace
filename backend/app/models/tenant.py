from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Tenant(Base, BaseModelMixin):
    __tablename__ = "tenant"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    requiere_aprobacion_comunicaciones: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
