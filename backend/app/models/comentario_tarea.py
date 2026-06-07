from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class ComentarioTarea(Base, TenantScopedModelMixin):
    __tablename__ = "comentario_tarea"

    tarea_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tarea.id"), nullable=False, index=True)
    autor_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    creado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ComentarioTarea id={self.id} tarea={self.tarea_id}>"
