from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoActivo


class Cohorte(Base, TenantScopedModelMixin):
    __tablename__ = "cohorte"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name="uq_cohorte_tenant_carrera_nombre"
        ),
    )

    carrera_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("carrera.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoActivo] = mapped_column(
        String(20), nullable=False, default=EstadoActivo.ACTIVA
    )
