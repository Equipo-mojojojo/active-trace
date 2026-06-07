from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, Integer, Uuid

from app.core.database import Base


class AuditLog(Base):
    """Append-only audit log for all significant actions.

    Immutable by design: the DB trigger ``no_audit_update_delete``
    rejects any UPDATE or DELETE on this table.
    """

    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenant.id"), nullable=False, index=True
    )
    actor_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("user_account.id"), nullable=False, index=True
    )
    impersonado_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("user_account.id"), nullable=True, index=True
    )
    materia_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )

    accion: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    filas_afectadas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    fecha_hora = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
