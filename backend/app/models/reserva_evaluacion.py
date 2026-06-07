from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoReserva


class ReservaEvaluacion(Base, TenantScopedModelMixin):
    __tablename__ = "reserva_evaluacion"

    turno_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("turno_evaluacion.id"), nullable=False, index=True)
    alumno_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False, index=True)
    estado: Mapped[EstadoReserva] = mapped_column(String(20), nullable=False, default=EstadoReserva.ACTIVA)

    def __repr__(self) -> str:
        return f"<ReservaEvaluacion id={self.id} estado={self.estado}>"
