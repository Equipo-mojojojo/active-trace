from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoActivo


class Carrera(Base, TenantScopedModelMixin):
    __tablename__ = "carrera"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carrera_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoActivo] = mapped_column(
        String(20), nullable=False, default=EstadoActivo.ACTIVA
    )
