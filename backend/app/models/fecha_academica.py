from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import TipoEvaluacion


class FechaAcademica(Base, TenantScopedModelMixin):
    __tablename__ = "fecha_academica"

    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cohorte.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoEvaluacion] = mapped_column(String(20), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
