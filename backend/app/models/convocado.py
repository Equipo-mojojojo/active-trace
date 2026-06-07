from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class Convocado(Base, TenantScopedModelMixin):
    __tablename__ = "convocado"
    __table_args__ = (
        UniqueConstraint("evaluacion_id", "alumno_id", name="uq_convocado_evaluacion_alumno"),
    )

    evaluacion_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("evaluacion.id"), nullable=False, index=True)
    alumno_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Convocado evaluacion={self.evaluacion_id} alumno={self.alumno_id}>"
