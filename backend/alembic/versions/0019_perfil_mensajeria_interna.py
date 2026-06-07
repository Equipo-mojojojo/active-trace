"""perfil fields and mensaje_interno table (C-20)

Revision ID: 0019_perfil_mensajeria_interna
Revises: 0018_seed_auditoria_finanzas_permission
Create Date: 2026-06-06 22:30:00

Alters:
- usuario: ADD COLUMN banco, regional, legajo_profesional, facturador, modalidad_cobro

Creates:
- mensaje_interno (inbox mensajería interna entre usuarios)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0019_perfil_mensajeria_interna"
down_revision = "0018_seed_auditoria_finanzas_permission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- alter usuario ---
    op.add_column("usuario", sa.Column("banco", sa.String(255), nullable=True))
    op.add_column("usuario", sa.Column("regional", sa.String(255), nullable=True))
    op.add_column("usuario", sa.Column("legajo_profesional", sa.String(50), nullable=True))
    op.add_column("usuario", sa.Column("facturador", sa.Boolean(), nullable=True, server_default="false"))
    op.add_column("usuario", sa.Column("modalidad_cobro", sa.String(20), nullable=True, server_default="liquidacion"))

    # --- mensaje_interno ---
    op.create_table(
        "mensaje_interno",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("hilo_id", sa.Uuid(), nullable=False),
        sa.Column("remitente_id", sa.Uuid(), nullable=False),
        sa.Column("destinatario_id", sa.Uuid(), nullable=False),
        sa.Column("asunto", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("leido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["remitente_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["destinatario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mensaje_interno_tenant_id", "mensaje_interno", ["tenant_id"])
    op.create_index("ix_mensaje_interno_hilo_id", "mensaje_interno", ["hilo_id"])
    op.create_index("ix_mensaje_interno_destinatario_id", "mensaje_interno", ["destinatario_id"])
    op.create_index("ix_mensaje_interno_remitente_id", "mensaje_interno", ["remitente_id"])
    op.create_index("ix_mensaje_interno_deleted_at", "mensaje_interno", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("mensaje_interno")
    op.drop_column("usuario", "modalidad_cobro")
    op.drop_column("usuario", "facturador")
    op.drop_column("usuario", "legajo_profesional")
    op.drop_column("usuario", "regional")
    op.drop_column("usuario", "banco")
