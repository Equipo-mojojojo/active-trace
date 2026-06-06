from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin
from app.models.enums import EstadoComunicacion


class InvalidStateTransitionError(Exception):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from '{current}' to '{target}'")


_VALID_TRANSITIONS: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
    EstadoComunicacion.PENDIENTE: {
        EstadoComunicacion.ENVIANDO,
        EstadoComunicacion.CANCELADO,
    },
    EstadoComunicacion.ENVIANDO: {
        EstadoComunicacion.ENVIADO,
        EstadoComunicacion.ERROR,
    },
    EstadoComunicacion.ENVIADO: set(),
    EstadoComunicacion.ERROR: set(),
    EstadoComunicacion.CANCELADO: set(),
}


class Comunicacion(Base, TenantScopedModelMixin):
    __tablename__ = "comunicacion"

    enviado_por: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    destinatario: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    asunto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoComunicacion] = mapped_column(
        String(20), nullable=False, default=EstadoComunicacion.PENDIENTE, index=True
    )
    lote_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    aprobado_por: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("usuario.id"), nullable=True
    )
    reintento_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

    def _transition(self, target: EstadoComunicacion) -> None:
        allowed = _VALID_TRANSITIONS.get(self.estado, set())
        if target not in allowed:
            raise InvalidStateTransitionError(str(self.estado), str(target))
        self.estado = target

    def marcar_enviando(self) -> None:
        self._transition(EstadoComunicacion.ENVIANDO)

    def marcar_enviado(self) -> None:
        self._transition(EstadoComunicacion.ENVIADO)
        self.enviado_at = datetime.now(timezone.utc)

    def marcar_error(self) -> None:
        self._transition(EstadoComunicacion.ERROR)

    def cancelar(self) -> None:
        self._transition(EstadoComunicacion.CANCELADO)
