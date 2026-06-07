from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class MensajeInterno(Base, TenantScopedModelMixin):
    __tablename__ = "mensaje_interno"

    hilo_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    remitente_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=False, index=True
    )
    destinatario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=False, index=True
    )
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    leido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
