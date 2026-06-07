from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class EstadoFactura(StrEnum):
    PENDIENTE = "pendiente"
    ABONADA = "abonada"


class Factura(Base, TenantScopedModelMixin):
    __tablename__ = "factura"

    usuario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=False, index=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_carga: Mapped[date] = mapped_column(Date, nullable=False)
    archivo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoFactura.PENDIENTE
    )
