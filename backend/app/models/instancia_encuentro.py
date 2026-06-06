from __future__ import annotations

from datetime import date, time
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoEncuentro


class InstanciaEncuentro(Base, TenantScopedModelMixin):
    """Encuentro concreto, derivado de un slot o creado de forma independiente.

    Cada instancia representa una ocurrencia real de un encuentro:
    - Si tiene slot_id, fue generada por un SlotEncuentro.
    - Si no tiene slot_id, es un encuentro único creado manualmente.

    El estado permite tracking: Programado → Realizado | Cancelado.
    """

    __tablename__ = "instancia_encuentro"

    slot_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("slot_encuentro.id"), nullable=True, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoEncuentro] = mapped_column(
        String(20), nullable=False, default=EstadoEncuentro.PROGRAMADO
    )
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<InstanciaEncuentro id={self.id} titulo={self.titulo!r} "
            f"fecha={self.fecha} estado={self.estado}>"
        )
