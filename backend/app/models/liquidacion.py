from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class EstadoLiquidacion(StrEnum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class Liquidacion(Base, TenantScopedModelMixin):
    __tablename__ = "liquidacion"

    cohorte_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    usuario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=False, index=True
    )
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    comisiones: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoLiquidacion.ABIERTA
    )

    @property
    def cerrada(self) -> bool:
        return self.estado == EstadoLiquidacion.CERRADA

    def cerrar(self) -> None:
        if self.cerrada:
            raise ValueError("liquidacion_cerrada")
        self.estado = EstadoLiquidacion.CERRADA
