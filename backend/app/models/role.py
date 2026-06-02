from __future__ import annotations

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class Role(Base, TenantScopedModelMixin):
    __tablename__ = "rol"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_rol_tenant_nombre"),
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    editable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
