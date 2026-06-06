from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class ProgramaMateria(Base, TenantScopedModelMixin):
    __tablename__ = "programa_materia"

    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    carrera_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("carrera.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cohorte.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    referencia_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
