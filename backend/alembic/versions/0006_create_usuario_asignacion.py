"""create usuario and asignacion tables for C-07

Revision ID: 0006_create_usuario_asignacion
Revises: 0005_create_estructura_academica
Create Date: 2026-06-03 18:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_create_usuario_asignacion"
down_revision = "0005_create_estructura_academica"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # usuario - Human identity with PII encryption
    # -----------------------------------------------------------------------
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("apellidos", sa.String(length=255), nullable=False),
        sa.Column("legajo", sa.String(length=50), nullable=True, unique=True),
        # PII - encrypted at rest via EncryptedString
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "email_lookup",
            sa.String(length=64),
            nullable=False,
            index=True,
        ),
        sa.Column("dni", sa.Text(), nullable=True),
        sa.Column("cuil", sa.Text(), nullable=True),
        sa.Column("cbu", sa.Text(), nullable=True),
        sa.Column("alias_cbu", sa.Text(), nullable=True),
        # Status
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="Activo"),
        # Timestamps and soft delete
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "email_lookup",
            name="uq_usuario_tenant_email_lookup",
        ),
    )
    # Indexes for common queries
    op.create_index(
        "idx_usuario_tenant",
        "usuario",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "idx_usuario_tenant_deleted",
        "usuario",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # -----------------------------------------------------------------------
    # asignacion - Role assignment with temporal validity
    # -----------------------------------------------------------------------
    op.create_table(
        "asignacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("rol", sa.String(length=50), nullable=False),
        # Optional context
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("carrera_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("comisiones", sa.String(length=500), nullable=True),
        # Temporal validity
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        # Hierarchy
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        # Timestamps and soft delete
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # Indexes for common queries
    op.create_index(
        "idx_asignacion_tenant",
        "asignacion",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "idx_asignacion_tenant_usuario",
        "asignacion",
        ["tenant_id", "usuario_id"],
        unique=False,
    )
    op.create_index(
        "idx_asignacion_vigor",
        "asignacion",
        ["tenant_id", "usuario_id", "desde", "hasta"],
        unique=False,
    )
    op.create_index(
        "idx_asignacion_deleted",
        "asignacion",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_asignacion_deleted", table_name="asignacion")
    op.drop_index("idx_asignacion_vigor", table_name="asignacion")
    op.drop_index("idx_asignacion_tenant_usuario", table_name="asignacion")
    op.drop_index("idx_asignacion_tenant", table_name="asignacion")

    op.drop_index("idx_usuario_tenant_deleted", table_name="usuario")
    op.drop_index("idx_usuario_tenant", table_name="usuario")

    # Drop tables
    op.drop_table("asignacion")
    op.drop_table("usuario")
