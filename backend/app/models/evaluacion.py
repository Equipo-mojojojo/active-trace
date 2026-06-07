from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoEvaluacion, TipoEvaluacion


class Evaluacion(Base, TenantScopedModelMixin):
    __tablename__ = "evaluacion"

    materia_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("materia.id"), nullable=False, index=True)
    cohorte_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("cohorte.id"), nullable=False, index=True)
    tipo: Mapped[TipoEvaluacion] = mapped_column(String(20), nullable=False)
    instancia: Mapped[str] = mapped_column(String(255), nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    estado: Mapped[EstadoEvaluacion] = mapped_column(String(20), nullable=False, default=EstadoEvaluacion.ABIERTA)

    def __repr__(self) -> str:
        return f"<Evaluacion id={self.id} tipo={self.tipo} instancia={self.instancia!r}>"
