"""create calificacion and umbral_materia tables (C-10)

Revision ID: 0008_create_calificacion_umbral_tables
Revises: 0007_create_padron_tables
Create Date: 2026-06-04 10:00:00

Tables:
  calificacion   — grade per (tenant, entrada_padron, actividad).
                   UNIQUE index on (tenant_id, entrada_padron_id, actividad)
                   guarantees idempotent upsert (D2).
  umbral_materia — approval threshold per assignment (D3).

Also seeds the 'calificaciones:importar' permission into the permission
catalog and assigns it to COORDINADOR, ADMIN, and PROFESOR roles.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0008_calificacion_umbral"
down_revision = "0007_create_padron_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # calificacion
    # -----------------------------------------------------------------------
    op.create_table(
        "calificacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("actividad", sa.String(length=500), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("nota_textual", sa.String(length=200), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "origen",
            sa.String(length=20),
            nullable=False,
            server_default="Importado",
        ),
        sa.Column(
            "importado_at",
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
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calificacion_tenant_id"), "calificacion", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_calificacion_entrada_padron_id"),
        "calificacion",
        ["entrada_padron_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_calificacion_materia_id"), "calificacion", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_calificacion_deleted_at"), "calificacion", ["deleted_at"], unique=False
    )

    # UNIQUE constraint for upsert idempotency (D2): one grade per student×activity
    op.execute(
        """
        CREATE UNIQUE INDEX uq_calificacion_entrada_actividad
        ON calificacion (tenant_id, entrada_padron_id, actividad)
        WHERE deleted_at IS NULL
        """
    )

    # -----------------------------------------------------------------------
    # umbral_materia
    # -----------------------------------------------------------------------
    op.create_table(
        "umbral_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column(
            "umbral_pct",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column(
            "valores_aprobatorios",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
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
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignacion.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_umbral_materia_tenant_id"), "umbral_materia", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_umbral_materia_asignacion_id"),
        "umbral_materia",
        ["asignacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_umbral_materia_deleted_at"), "umbral_materia", ["deleted_at"], unique=False
    )

    # One threshold per assignment
    op.execute(
        """
        CREATE UNIQUE INDEX uq_umbral_materia_asignacion
        ON umbral_materia (tenant_id, asignacion_id)
        WHERE deleted_at IS NULL
        """
    )

    # -----------------------------------------------------------------------
    # Seed: calificaciones:importar permission + role assignments
    # -----------------------------------------------------------------------
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return

    default_tenant_id = str(row[0])

    existing = conn.execute(
        sa.text(
            "SELECT id FROM permiso WHERE codigo = 'calificaciones:importar' AND tenant_id = :tid"
        ),
        {"tid": default_tenant_id},
    ).fetchone()

    if existing:
        perm_id = str(existing[0])
    else:
        perm_id = str(uuid4())
        conn.execute(
            sa.text(
                """INSERT INTO permiso (id, tenant_id, codigo, modulo, accion, descripcion)
                   VALUES (:id, :tenant_id, :codigo, :modulo, :accion, :descripcion)"""
            ),
            {
                "id": perm_id,
                "tenant_id": default_tenant_id,
                "codigo": "calificaciones:importar",
                "modulo": "calificaciones",
                "accion": "importar",
                "descripcion": "Importar y gestionar calificaciones desde el LMS",
            },
        )

    for role_name in ("COORDINADOR", "ADMIN", "PROFESOR"):
        role_row = conn.execute(
            sa.text("SELECT id FROM rol WHERE nombre = :nombre AND tenant_id = :tid"),
            {"nombre": role_name, "tid": default_tenant_id},
        ).fetchone()

        if role_row is None:
            continue

        role_id = str(role_row[0])

        already = conn.execute(
            sa.text(
                """SELECT id FROM rol_permiso
                   WHERE rol_id = :rid AND permiso_id = :pid AND tenant_id = :tid"""
            ),
            {"rid": role_id, "pid": perm_id, "tid": default_tenant_id},
        ).fetchone()

        if already:
            continue

        conn.execute(
            sa.text(
                """INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id)
                   VALUES (:id, :tenant_id, :rol_id, :permiso_id)"""
            ),
            {
                "id": str(uuid4()),
                "tenant_id": default_tenant_id,
                "rol_id": role_id,
                "permiso_id": perm_id,
            },
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_umbral_materia_asignacion")
    op.execute("DROP INDEX IF EXISTS uq_calificacion_entrada_actividad")

    op.drop_index(op.f("ix_umbral_materia_deleted_at"), table_name="umbral_materia")
    op.drop_index(op.f("ix_umbral_materia_asignacion_id"), table_name="umbral_materia")
    op.drop_index(op.f("ix_umbral_materia_tenant_id"), table_name="umbral_materia")
    op.drop_table("umbral_materia")

    op.drop_index(op.f("ix_calificacion_deleted_at"), table_name="calificacion")
    op.drop_index(op.f("ix_calificacion_materia_id"), table_name="calificacion")
    op.drop_index(op.f("ix_calificacion_entrada_padron_id"), table_name="calificacion")
    op.drop_index(op.f("ix_calificacion_tenant_id"), table_name="calificacion")
    op.drop_table("calificacion")
