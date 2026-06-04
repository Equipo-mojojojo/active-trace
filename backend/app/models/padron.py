"""
Padron ORM models for C-09: VersionPadron + EntradaPadron.

VersionPadron: versioned roster per (tenant, materia, cohorte).
  - At most one activa=True per (tenant_id, materia_id, cohorte_id).
  - Activating a new version soft-deactivates the previous one (D1).

EntradaPadron: individual student row within a version.
  - usuario_id may be NULL (alumno sin cuenta de usuario, spec req E2).
  - email is PII -> stored encrypted via EncryptedString (D6 / hard rule).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin


class VersionPadron(Base, TenantScopedModelMixin):
    """Versioned roster for a (materia, cohorte) pair within a tenant.

    Invariant: at most one row with activa=True per
    (tenant_id, materia_id, cohorte_id).  Enforced by the partial unique
    index in migration 007 and by PadronRepository.desactivar_version_activa().
    """

    __tablename__ = "version_padron"

    # Foreign keys
    materia_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("materia.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cohorte.id"), nullable=False, index=True
    )

    # State
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    cargado_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    total_entradas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="archivo"
    )  # 'archivo' | 'moodle'

    def __repr__(self) -> str:
        return (
            f"<VersionPadron id={self.id} "
            f"materia_id={self.materia_id} "
            f"cohorte_id={self.cohorte_id} "
            f"activa={self.activa}>"
        )


class EntradaPadron(Base, TenantScopedModelMixin):
    """Individual student entry within a VersionPadron.

    usuario_id is NULL when the student has no account yet (spec req E2).
    email is encrypted at rest (AES-256) via EncryptedString.
    """

    __tablename__ = "entrada_padron"

    # Parent version
    version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("version_padron.id"), nullable=False, index=True
    )

    # Optional link to an existing Usuario account
    usuario_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    # Student data — nombre/apellidos plaintext; email PII encrypted
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)

    # Academic context (denormalised from file row)
    comision: Mapped[str | None] = mapped_column(String(100), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EntradaPadron id={self.id} "
            f"version_id={self.version_id} "
            f"nombre={self.nombre}>"
        )
