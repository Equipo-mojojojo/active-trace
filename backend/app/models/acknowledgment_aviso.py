from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class AcknowledgmentAviso(Base, TenantScopedModelMixin):
    __tablename__ = "acknowledgment_aviso"
    __table_args__ = (
        UniqueConstraint("aviso_id", "usuario_id", name="uq_ack_aviso_usuario"),
    )

    aviso_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("aviso.id"), nullable=False, index=True)
    usuario_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"), nullable=False, index=True)
    confirmado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AcknowledgmentAviso aviso={self.aviso_id} usuario={self.usuario_id}>"
