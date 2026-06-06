"""create version_padron and entrada_padron tables (C-09)

Revision ID: 0007_create_padron_tables
Revises: 0006_create_usuario_asignacion
Create Date: 2026-06-03 20:00:00

Tables:
  version_padron  — versioned roster per (tenant, materia, cohorte).
                    Partial unique index ensures at most one activa=true
                    per (tenant_id, materia_id, cohorte_id).
  entrada_padron  — individual student rows; email encrypted at rest.

Also seeds the 'padron:importar' permission into the permission catalog
and assigns it to COORDINADOR, ADMIN, and PROFESOR roles.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0007_create_padron_tables"
down_revision = "0006_create_usuario_asignacion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # version_padron
    # -----------------------------------------------------------------------
    op.create_table(
        "version_padron",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("total_entradas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cargado_by", sa.Uuid(), nullable=True),
        sa.Column(
            "origen",
            sa.String(length=20),
            nullable=False,
            server_default="archivo",
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
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_version_padron_tenant_id"), "version_padron", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_version_padron_materia_id"), "version_padron", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_version_padron_cohorte_id"), "version_padron", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_version_padron_deleted_at"), "version_padron", ["deleted_at"], unique=False
    )

    # Partial unique index — at most one activa=true per (tenant_id, materia_id, cohorte_id).
    # autogenerate cannot detect partial indexes, so we create it manually.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_version_padron_activa
        ON version_padron (tenant_id, materia_id, cohorte_id)
        WHERE activa = true AND deleted_at IS NULL
        """
    )

    # -----------------------------------------------------------------------
    # entrada_padron
    # -----------------------------------------------------------------------
    op.create_table(
        "entrada_padron",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("apellidos", sa.String(length=255), nullable=False),
        # email is Text because EncryptedString uses Text impl
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("comision", sa.String(length=100), nullable=True),
        sa.Column("regional", sa.String(length=100), nullable=True),
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
        sa.ForeignKeyConstraint(["version_id"], ["version_padron.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_entrada_padron_tenant_id"), "entrada_padron", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_entrada_padron_version_id"), "entrada_padron", ["version_id"], unique=False
    )
    op.create_index(
        op.f("ix_entrada_padron_deleted_at"), "entrada_padron", ["deleted_at"], unique=False
    )

    # -----------------------------------------------------------------------
    # Seed: padron:importar permission + role assignments
    # -----------------------------------------------------------------------
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return  # No tenant to seed — skip

    default_tenant_id = str(row[0])

    # Check if padron:importar already exists
    existing = conn.execute(
        sa.text(
            "SELECT id FROM permiso WHERE codigo = 'padron:importar' AND tenant_id = :tid"
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
                "codigo": "padron:importar",
                "modulo": "padron",
                "accion": "importar",
                "descripcion": "Importar y gestionar el padrón de alumnos",
            },
        )

    # Assign padron:importar to COORDINADOR, ADMIN, PROFESOR roles
    for role_name in ("COORDINADOR", "ADMIN", "PROFESOR"):
        role_row = conn.execute(
            sa.text(
                "SELECT id FROM rol WHERE nombre = :nombre AND tenant_id = :tid"
            ),
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
    op.execute("DROP INDEX IF EXISTS uq_version_padron_activa")

    op.drop_index(op.f("ix_entrada_padron_deleted_at"), table_name="entrada_padron")
    op.drop_index(op.f("ix_entrada_padron_version_id"), table_name="entrada_padron")
    op.drop_index(op.f("ix_entrada_padron_tenant_id"), table_name="entrada_padron")
    op.drop_table("entrada_padron")

    op.drop_index(op.f("ix_version_padron_deleted_at"), table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_cohorte_id"), table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_materia_id"), table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_tenant_id"), table_name="version_padron")
    op.drop_table("version_padron")
