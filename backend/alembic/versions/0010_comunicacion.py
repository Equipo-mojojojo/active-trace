"""create comunicacion table (C-12)

Revision ID: 0010_comunicacion
Revises: 0009_seed_atrasados_permission
Create Date: 2026-06-06 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0010_comunicacion"
down_revision = "0009_seed_atrasados_permission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant",
        sa.Column(
            "communication_approval_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "comunicacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("lote_id", sa.Uuid(), nullable=False),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("destinatario_email", sa.Text(), nullable=False),
        sa.Column("destinatario_nombre", sa.String(length=255), nullable=False),
        sa.Column("asunto", sa.String(length=255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "estado", sa.String(length=20), nullable=False, server_default="Pendiente"
        ),
        sa.Column(
            "requiere_aprobacion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("aprobada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aprobada_por", sa.Uuid(), nullable=True),
        sa.Column("cancelada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelada_por", sa.Uuid(), nullable=True),
        sa.Column("enviada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detalle", sa.Text(), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["aprobada_por"], ["user_account.id"]),
        sa.ForeignKeyConstraint(["cancelada_por"], ["user_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comunicacion_tenant_id"), "comunicacion", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_comunicacion_lote_id"), "comunicacion", ["lote_id"], unique=False
    )
    op.create_index(
        op.f("ix_comunicacion_entrada_padron_id"),
        "comunicacion",
        ["entrada_padron_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comunicacion_materia_id"), "comunicacion", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_comunicacion_deleted_at"), "comunicacion", ["deleted_at"], unique=False
    )
    op.create_index(
        "ix_comunicacion_tenant_estado",
        "comunicacion",
        ["tenant_id", "estado"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comunicacion_tenant_estado", table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_deleted_at"), table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_materia_id"), table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_entrada_padron_id"), table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_lote_id"), table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_tenant_id"), table_name="comunicacion")
    op.drop_table("comunicacion")
    op.drop_column("tenant", "communication_approval_required")
