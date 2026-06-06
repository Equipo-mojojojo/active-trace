"""create comunicacion table (C-12)

Revision ID: 0010_comunicacion
Revises: 0009_seed_atrasados_permission
Create Date: 2026-06-06 00:00:00

DDL changes:
  1. Add tenant.requiere_aprobacion_comunicaciones BOOLEAN NOT NULL DEFAULT false
  2. Create comunicacion table with full state-machine fields
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_comunicacion"
down_revision = "0009_seed_atrasados_permission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Extend tenant table
    op.add_column(
        "tenant",
        sa.Column(
            "requiere_aprobacion_comunicaciones",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # 2. Create comunicacion table
    op.create_table(
        "comunicacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("enviado_por", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("destinatario", sa.Text(), nullable=False),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column("lote_id", sa.Uuid(), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aprobado_por", sa.Uuid(), nullable=True),
        sa.Column("reintento_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["enviado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["aprobado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_comunicacion_tenant", "comunicacion", ["tenant_id"])
    op.create_index("idx_comunicacion_lote", "comunicacion", ["lote_id"])
    op.create_index("idx_comunicacion_estado", "comunicacion", ["estado"])
    op.create_index("idx_comunicacion_enviado_por", "comunicacion", ["enviado_por"])
    op.create_index("idx_comunicacion_materia", "comunicacion", ["materia_id"])
    op.create_index("idx_comunicacion_deleted", "comunicacion", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("comunicacion")
    op.drop_column("tenant", "requiere_aprobacion_comunicaciones")
