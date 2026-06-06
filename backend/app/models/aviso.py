from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import AlcanceAviso, SeveridadAviso


class Aviso(Base, TenantScopedModelMixin):
    __tablename__ = "aviso"

    alcance: Mapped[AlcanceAviso] = mapped_column(String(20), nullable=False)
    materia_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("materia.id"), nullable=True)
    cohorte_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("cohorte.id"), nullable=True)
    rol_destino: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severidad: Mapped[SeveridadAviso] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<Aviso id={self.id} titulo={self.titulo!r} alcance={self.alcance}>"
