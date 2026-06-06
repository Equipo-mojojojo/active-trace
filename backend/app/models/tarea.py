from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoTarea


class Tarea(Base, TenantScopedModelMixin):
    __tablename__ = "tarea"

    materia_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("materia.id"), nullable=True)
    asignado_a: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False, index=True)
    asignado_por: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False)
    estado: Mapped[EstadoTarea] = mapped_column(String(20), nullable=False, default=EstadoTarea.PENDIENTE)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    def __repr__(self) -> str:
        return f"<Tarea id={self.id} estado={self.estado} asignado_a={self.asignado_a}>"
