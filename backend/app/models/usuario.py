"""
Usuario ORM model for C-07: Human identity with PII encryption.

Inherits TenantScopedModelMixin for multi-tenancy and soft delete.
PII fields (email, dni, cbu, cuil) are encrypted using AES-256 via EncryptedString.
"""

from __future__ import annotations

from sqlalchemy import String, UniqueConstraint, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base
from app.core.security import EncryptedString, build_email_lookup
from app.models.base import TenantScopedModelMixin


class UsuarioEstado(str, enum.Enum):
    """Estado enum for Usuario: Activo or Inactivo."""
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Usuario(Base, TenantScopedModelMixin):
    """
    Usuario: Human identity model with PII encryption.

    All sensitive fields (email, dni, cbu, cuil, alias_cbu) are encrypted at rest
    using AES-256 (via EncryptedString SQLAlchemy type).

    Email uniqueness is enforced per tenant via email_lookup (HMAC-based hash).
    Legajo is a business attribute (not a credential or PK).

    Inherits:
    - tenant_id (from TenantScopedModelMixin)
    - id, created_at, updated_at, deleted_at (from BaseModelMixin)
    """

    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email_lookup",
            name="uq_usuario_tenant_email_lookup",
        ),
        Index("idx_usuario_tenant", "tenant_id"),
        Index("idx_usuario_tenant_deleted", "tenant_id", "deleted_at"),
    )

    # Personal info (plaintext)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(255), nullable=False)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    # PII - encrypted at rest
    email: Mapped[str] = mapped_column(EncryptedString(), nullable=False)
    email_lookup: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # HMAC-based lookup
    dni: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    cuil: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    cbu: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
    alias_cbu: Mapped[str | None] = mapped_column(
        EncryptedString(), nullable=True
    )  # Alias for CBU

    # Profile fields
    banco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legajo_profesional: Mapped[str | None] = mapped_column(String(50), nullable=True)
    facturador: Mapped[bool] = mapped_column(nullable=False, default=False)
    modalidad_cobro: Mapped[str] = mapped_column(String(20), nullable=False, default="liquidacion")

    # Status
    estado: Mapped[UsuarioEstado] = mapped_column(
        SQLEnum(UsuarioEstado),
        nullable=False,
        default=UsuarioEstado.ACTIVO,
    )

    def __init__(
        self,
        tenant_id,
        nombre: str,
        apellidos: str,
        email: str,
        dni: str | None = None,
        cuil: str | None = None,
        cbu: str | None = None,
        alias_cbu: str | None = None,
        legajo: str | None = None,
        estado: UsuarioEstado = UsuarioEstado.ACTIVO,
    ):
        """Initialize Usuario with automatic email_lookup hash."""
        self.tenant_id = tenant_id
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email
        self.email_lookup = build_email_lookup(email)
        self.dni = dni
        self.cuil = cuil
        self.cbu = cbu
        self.alias_cbu = alias_cbu
        self.legajo = legajo
        self.estado = estado

    def __repr__(self) -> str:
        """String representation without exposing PII."""
        return f"<Usuario id={self.id} nombre={self.nombre} tenant_id={self.tenant_id}>"
