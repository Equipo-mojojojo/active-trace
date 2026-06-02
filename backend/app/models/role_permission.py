from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class RolePermission(Base, TenantScopedModelMixin):
    __tablename__ = "rol_permiso"
    __table_args__ = (
        UniqueConstraint(
            "rol_id",
            "permiso_id",
            "tenant_id",
            name="uq_rol_permiso_tenant",
        ),
    )

    rol_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("rol.id"), nullable=False, index=True
    )
    permiso_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("permiso.id"), nullable=False, index=True
    )
