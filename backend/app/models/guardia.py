from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import DiaSemana, EstadoGuardia


class Guardia(Base, TenantScopedModelMixin):
    """Registro de una guardia de atención a alumnos.

    Las guardias son cubiertas por tutores/docentes y registran
    cuándo y en qué contexto se brindó atención a alumnos.
    """

    __tablename__ = "guardia"

    asignacion_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("asignacion.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    carrera_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("carrera.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cohorte.id"), nullable=False, index=True
    )
    dia: Mapped[DiaSemana] = mapped_column(String(20), nullable=False)
    horario: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoGuardia] = mapped_column(
        String(20), nullable=False, default=EstadoGuardia.PENDIENTE
    )
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Guardia id={self.id} asignacion_id={self.asignacion_id} "
            f"dia={self.dia} estado={self.estado}>"
        )
