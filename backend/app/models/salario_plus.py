from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class SalarioPlus(Base, TenantScopedModelMixin):
    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
