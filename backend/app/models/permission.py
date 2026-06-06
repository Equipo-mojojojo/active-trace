from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class Permission(Base, TenantScopedModelMixin):
    __tablename__ = "permiso"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_permiso_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
