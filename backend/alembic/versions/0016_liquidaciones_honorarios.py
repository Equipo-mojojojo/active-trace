"""create liquidaciones y honorarios tables (C-18)

Revision ID: 0016_liquidaciones_honorarios
Revises: 0015_create_programa_materia_fecha_academica
Create Date: 2026-06-06 21:00:00

Creates tables:
- salario_base (grilla base por rol con vigencia)
- salario_plus (plus por grupo×rol con vigencia)
- liquidacion (liquidacion de honorarios por periodo)
- factura (comprobantes de docentes que facturan)

Alters tables:
- materia: ADD COLUMN grupo_plus_clave TEXT NULL
- tenant: ADD COLUMN tope_plus INTEGER NULL
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_liquidaciones_honorarios"
down_revision = "0015_create_programa_materia_fecha_academica"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- salario_base ---
    op.create_table(
        "salario_base",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_salario_base_tenant_id", "salario_base", ["tenant_id"])
    op.create_index("ix_salario_base_deleted_at", "salario_base", ["deleted_at"])
    op.create_index("ix_salario_base_rol", "salario_base", ["rol"])

    # --- salario_plus ---
    op.create_table(
        "salario_plus",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("grupo", sa.String(100), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_salario_plus_tenant_id", "salario_plus", ["tenant_id"])
    op.create_index("ix_salario_plus_deleted_at", "salario_plus", ["deleted_at"])
    op.create_index("ix_salario_plus_grupo_rol", "salario_plus", ["grupo", "rol"])

    # --- liquidacion ---
    op.create_table(
        "liquidacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("comisiones", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("monto_base", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "excluido_por_factura",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Abierta"),
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
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_liquidacion_tenant_id", "liquidacion", ["tenant_id"])
    op.create_index("ix_liquidacion_periodo", "liquidacion", ["periodo"])
    op.create_index("ix_liquidacion_usuario_id", "liquidacion", ["usuario_id"])
    op.create_index("ix_liquidacion_deleted_at", "liquidacion", ["deleted_at"])

    # --- factura ---
    op.create_table(
        "factura",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("fecha_carga", sa.Date(), nullable=False),
        sa.Column("archivo_path", sa.String(512), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
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
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_factura_tenant_id", "factura", ["tenant_id"])
    op.create_index("ix_factura_usuario_id", "factura", ["usuario_id"])
    op.create_index("ix_factura_periodo", "factura", ["periodo"])
    op.create_index("ix_factura_deleted_at", "factura", ["deleted_at"])

    # --- alter materia: add grupo_plus_clave ---
    op.add_column("materia", sa.Column("grupo_plus_clave", sa.String(100), nullable=True))

    # --- alter tenant: add tope_plus ---
    op.add_column("tenant", sa.Column("tope_plus", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenant", "tope_plus")
    op.drop_column("materia", "grupo_plus_clave")
    op.drop_table("factura")
    op.drop_table("liquidacion")
    op.drop_table("salario_plus")
    op.drop_table("salario_base")
