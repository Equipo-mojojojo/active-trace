"""
ORM models for C-10: Calificacion + UmbralMateria.

Calificacion: grade per (tenant, entrada_padron, actividad).
  - aprobado is computed on write, not derived on read (D1).
  - origen: Importado | Manual.
  - UNIQUE index (tenant_id, entrada_padron_id, actividad) enforced by migration.

UmbralMateria: approval threshold per assignment (D3).
  - Scoped to Asignacion, not to (usuario_id, materia_id) directly.
  - umbral_pct default: 60. valores_aprobatorios default: [] (service fills default).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedModelMixin

DEFAULT_UMBRAL_PCT = 60
DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]


class Calificacion(Base, TenantScopedModelMixin):
    """Grade record for one student × activity combination within a materia."""

    __tablename__ = "calificacion"

    entrada_padron_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("entrada_padron.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )

    actividad: Mapped[str] = mapped_column(String(500), nullable=False)
    nota_numerica: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=4), nullable=True
    )
    nota_textual: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Computed at write time (D1) — not a DB computed column.
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Importado"
    )  # "Importado" | "Manual"
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Calificacion id={self.id} "
            f"entrada_padron_id={self.entrada_padron_id} "
            f"actividad={self.actividad!r} "
            f"aprobado={self.aprobado}>"
        )


class UmbralMateria(Base, TenantScopedModelMixin):
    """Approval threshold for a specific assignment (docente × materia × period).

    Isolation rule (RN-04): one row per Asignacion.
    If no row exists for an assignment, the service falls back to DEFAULT_UMBRAL_PCT.
    """

    __tablename__ = "umbral_materia"

    asignacion_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("asignacion.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False
    )

    umbral_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=DEFAULT_UMBRAL_PCT
    )
    valores_aprobatorios: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), nullable=False, default=list
    )

    def __repr__(self) -> str:
        return (
            f"<UmbralMateria id={self.id} "
            f"asignacion_id={self.asignacion_id} "
            f"umbral_pct={self.umbral_pct}>"
        )
