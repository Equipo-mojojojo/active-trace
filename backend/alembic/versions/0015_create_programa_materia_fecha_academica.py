"""create programa_materia and fecha_academica tables (C-17)

Revision ID: 0015_create_programa_materia_fecha_academica
Revises: 0014_tareas_internas
Create Date: 2026-06-06 16:00:00

Creates tables:
- programa_materia (programs/documents for each subject, carrera, cohorte)
- fecha_academica (academic evaluation dates)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_create_programa_materia_fecha_academica"
down_revision = "0014_tareas_internas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- programa_materia ---
    op.create_table(
        "programa_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("referencia_archivo", sa.String(255), nullable=False),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_programa_materia_tenant_id"), "programa_materia", ["tenant_id"]
    )
    op.create_index(
        op.f("ix_programa_materia_deleted_at"), "programa_materia", ["deleted_at"]
    )
    op.create_index(
        op.f("ix_programa_materia_materia_id"), "programa_materia", ["materia_id"]
    )
    op.create_index(
        op.f("ix_programa_materia_carrera_id"), "programa_materia", ["carrera_id"]
    )
    op.create_index(
        op.f("ix_programa_materia_cohorte_id"), "programa_materia", ["cohorte_id"]
    )

    # --- fecha_academica ---
    op.create_table(
        "fecha_academica",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
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
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fecha_academica_tenant_id"), "fecha_academica", ["tenant_id"]
    )
    op.create_index(
        op.f("ix_fecha_academica_deleted_at"), "fecha_academica", ["deleted_at"]
    )
    op.create_index(
        op.f("ix_fecha_academica_materia_id"), "fecha_academica", ["materia_id"]
    )
    op.create_index(
        op.f("ix_fecha_academica_cohorte_id"), "fecha_academica", ["cohorte_id"]
    )


def downgrade() -> None:
    op.drop_table("fecha_academica")
    op.drop_table("programa_materia")
