from __future__ import annotations

from datetime import date, time
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class TurnoEvaluacion(Base, TenantScopedModelMixin):
    __tablename__ = "turno_evaluacion"

    evaluacion_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("evaluacion.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    max_cupo: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    def __repr__(self) -> str:
        return f"<TurnoEvaluacion id={self.id} fecha={self.fecha} hora={self.hora} cupo={self.max_cupo}>"
