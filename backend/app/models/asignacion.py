"""
Asignacion ORM model for C-07: Role assignment with temporal validity.

Represents the binding of a Usuario to a Role in a specific Context (materia/carrera/cohorte)
with temporal validity (desde/hasta dates).

estado_vigencia is computed (not stored): Vigente, Futura, or Vencida.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import String, Date, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base
from app.models.base import TenantScopedModelMixin


class RolEnum(str, enum.Enum):
    """Rol values: PROFESOR, TUTOR, COORDINADOR, NEXO, ADMIN, ALUMNO."""
    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    COORDINADOR = "COORDINADOR"
    NEXO = "NEXO"
    ADMIN = "ADMIN"
    ALUMNO = "ALUMNO"


class Asignacion(Base, TenantScopedModelMixin):
    """
    Asignacion: Role assignment with temporal validity.

    A Usuario can have multiple Asignaciones with different roles, contexts, and dates.
    estado_vigencia is computed based on today's date vs. desde/hasta.

    Inherits:
    - tenant_id (from TenantScopedModelMixin)
    - id, created_at, updated_at, deleted_at (from BaseModelMixin)
    """

    __tablename__ = "asignacion"
    __table_args__ = (
        Index("idx_asignacion_tenant", "tenant_id"),
        Index("idx_asignacion_tenant_usuario", "tenant_id", "usuario_id"),
        Index(
            "idx_asignacion_vigor",
            "tenant_id",
            "usuario_id",
            "desde",
            "hasta",
        ),
        Index("idx_asignacion_deleted", "tenant_id", "deleted_at"),
    )

    # Foreign key to Usuario
    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id"), nullable=False, index=True
    )

    # Role and context
    rol: Mapped[RolEnum] = mapped_column(String(50), nullable=False)

    # Optional context fields (materia, carrera, cohorte, comisiones)
    materia_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("materia.id"), nullable=True
    )
    carrera_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("carrera.id"), nullable=True
    )
    cohorte_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cohorte.id"), nullable=True
    )
    comisiones: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Temporal validity
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Hierarchy: responsable_id points to another Usuario
    responsable_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True
    )

    @property
    def estado_vigencia(self) -> str:
        """
        Computed property: estado_vigencia based on today's date.

        Returns:
        - "Vigente" if desde <= today and (hasta is None or today < hasta)
        - "Futura" if today < desde
        - "Vencida" if hasta is not None and today >= hasta
        """
        today = date.today()

        if today < self.desde:
            return "Futura"

        if self.hasta is not None and today >= self.hasta:
            return "Vencida"

        return "Vigente"

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Asignacion id={self.id} usuario_id={self.usuario_id} "
            f"rol={self.rol} estado={self.estado_vigencia}>"
        )
