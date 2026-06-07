from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin, utc_now


class EstadoComunicacion(StrEnum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class Comunicacion(Base, TenantScopedModelMixin):
    __tablename__ = "comunicacion"

    lote_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    entrada_padron_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("entrada_padron.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )

    destinatario_email: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    destinatario_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)

    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoComunicacion.PENDIENTE
    )
    requiere_aprobacion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    aprobada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    aprobada_por: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("user_account.id"), nullable=True
    )
    cancelada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelada_por: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("user_account.id"), nullable=True
    )
    enviada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    @property
    def aprobada(self) -> bool:
        return self.aprobada_at is not None

    @property
    def elegible_para_worker(self) -> bool:
        if self.estado != EstadoComunicacion.PENDIENTE:
            return False
        if not self.requiere_aprobacion:
            return True
        return self.aprobada

    def aprobar(self, actor_id: UUID) -> None:
        if self.estado != EstadoComunicacion.PENDIENTE:
            raise ValueError("Solo se pueden aprobar comunicaciones pendientes")
        if not self.requiere_aprobacion:
            raise ValueError("La comunicación no requiere aprobación")
        self.aprobada_at = utc_now()
        self.aprobada_por = actor_id

    def cancelar(self, actor_id: UUID) -> None:
        if self.estado != EstadoComunicacion.PENDIENTE:
            raise ValueError("Solo se pueden cancelar comunicaciones pendientes")
        self.estado = EstadoComunicacion.CANCELADO
        self.cancelada_at = utc_now()
        self.cancelada_por = actor_id

    def marcar_enviando(self) -> None:
        if not self.elegible_para_worker:
            raise ValueError("La comunicación no es elegible para envío")
        self.estado = EstadoComunicacion.ENVIANDO
        self.intentos = (self.intentos or 0) + 1
        self.error_detalle = None

    def marcar_enviada(self) -> None:
        if self.estado != EstadoComunicacion.ENVIANDO:
            raise ValueError("Solo se pueden finalizar comunicaciones en envío")
        self.estado = EstadoComunicacion.ENVIADO
        self.enviada_at = utc_now()
        self.error_detalle = None

    def marcar_error(self, detalle: str) -> None:
        if self.estado != EstadoComunicacion.ENVIANDO:
            raise ValueError("Solo se pueden marcar errores desde Enviando")
        self.estado = EstadoComunicacion.ERROR
        self.error_detalle = detalle

    def __repr__(self) -> str:
        return (
            f"<Comunicacion id={self.id} lote_id={self.lote_id} "
            f"estado={self.estado} materia_id={self.materia_id}>"
        )
