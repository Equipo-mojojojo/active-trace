from __future__ import annotations

from datetime import date, time
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import DiaSemana


class SlotEncuentro(Base, TenantScopedModelMixin):
    """Plantilla que define la recurrencia de un encuentro sincrónico.

    Un slot puede ser:
    - Recurrente: con cant_semanas > 0 y fecha_inicio.
    - Fecha única: con cant_semanas = 0 y fecha_unica no nula.

    Al crear un slot recurrente, el servicio genera automáticamente
    todas las instancias (InstanciaEncuentro).
    """

    __tablename__ = "slot_encuentro"

    asignacion_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("asignacion.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    dia_semana: Mapped[DiaSemana] = mapped_column(String(20), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    cant_semanas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SlotEncuentro id={self.id} titulo={self.titulo!r} "
            f"dia={self.dia_semana} hora={self.hora}>"
        )
