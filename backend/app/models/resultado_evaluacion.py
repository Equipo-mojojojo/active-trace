from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class ResultadoEvaluacion(Base, TenantScopedModelMixin):
    __tablename__ = "resultado_evaluacion"

    evaluacion_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("evaluacion.id"), nullable=False, index=True)
    alumno_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False, index=True)
    nota_final: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<ResultadoEvaluacion evaluacion={self.evaluacion_id} alumno={self.alumno_id}>"
