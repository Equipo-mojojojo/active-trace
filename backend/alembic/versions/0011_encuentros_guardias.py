"""create encuentros and guardias tables (C-13)

Revision ID: 0011_encuentros_guardias
Revises: 0010_comunicacion
Create Date: 2026-06-06 11:00:00

Creates tables:
- slot_encuentro (E9)
- instancia_encuentro (E10)
- guardia (E11)

Seeds permissions:
- encuentros:gestionar, encuentros:ver, guardias:registrar

Audit codes (used as strings in audit service):
- ENCUENTRO_CREAR, ENCUENTRO_EDITAR, GUARDIA_REGISTRAR
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_encuentros_guardias"
down_revision = "0010_comunicacion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- slot_encuentro ---
    op.create_table(
        "slot_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("dia_semana", sa.String(20), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("cant_semanas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fecha_unica", sa.Date(), nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
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
        op.f("ix_slot_encuentro_tenant_id"),
        "slot_encuentro",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slot_encuentro_asignacion_id"),
        "slot_encuentro",
        ["asignacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slot_encuentro_materia_id"),
        "slot_encuentro",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slot_encuentro_deleted_at"),
        "slot_encuentro",
        ["deleted_at"],
        unique=False,
    )

    # --- instancia_encuentro ---
    op.create_table(
        "instancia_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slot_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Programado",
        ),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["slot_id"], ["slot_encuentro.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_instancia_encuentro_tenant_id"),
        "instancia_encuentro",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instancia_encuentro_slot_id"),
        "instancia_encuentro",
        ["slot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instancia_encuentro_materia_id"),
        "instancia_encuentro",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instancia_encuentro_fecha"),
        "instancia_encuentro",
        ["fecha"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instancia_encuentro_deleted_at"),
        "instancia_encuentro",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_estado",
        "instancia_encuentro",
        ["tenant_id", "estado"],
        unique=False,
    )

    # --- guardia ---
    op.create_table(
        "guardia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("dia", sa.String(20), nullable=False),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("comentarios", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guardia_tenant_id"), "guardia", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_guardia_asignacion_id"),
        "guardia",
        ["asignacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guardia_materia_id"), "guardia", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_guardia_carrera_id"), "guardia", ["carrera_id"], unique=False
    )
    op.create_index(
        op.f("ix_guardia_cohorte_id"), "guardia", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_guardia_deleted_at"), "guardia", ["deleted_at"], unique=False
    )

    conn = op.get_bind()
    _seed_permissions(conn)


def _seed_permissions(conn) -> None:
    """Seed permissions for encuentros and guardias modules.

    Assigns:
    - encuentros:gestionar → PROFESOR, COORDINADOR
    - encuentros:ver → TUTOR, PROFESOR, COORDINADOR, ADMIN
    - guardias:registrar → TUTOR (propio), COORDINADOR (global)
    """
    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return

    default_tenant_id = str(row[0])

    permissions = [
        {
            "codigo": "encuentros:gestionar",
            "modulo": "encuentros",
            "accion": "gestionar",
            "descripcion": "Crear, editar y eliminar encuentros (slots e instancias)",
            "roles": ["PROFESOR", "COORDINADOR"],
        },
        {
            "codigo": "encuentros:ver",
            "modulo": "encuentros",
            "accion": "ver",
            "descripcion": "Ver encuentros del equipo docente",
            "roles": ["TUTOR", "PROFESOR", "COORDINADOR", "ADMIN"],
        },
        {
            "codigo": "guardias:registrar",
            "modulo": "guardias",
            "accion": "registrar",
            "descripcion": "Registrar guardias de atención (propias) y gestionarlas",
            "roles": ["TUTOR", "COORDINADOR"],
        },
    ]

    for perm in permissions:
        existing = conn.execute(
            sa.text(
                "SELECT id FROM permiso WHERE codigo = :codigo AND tenant_id = :tid"
            ),
            {"codigo": perm["codigo"], "tid": default_tenant_id},
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
                    "codigo": perm["codigo"],
                    "modulo": perm["modulo"],
                    "accion": perm["accion"],
                    "descripcion": perm["descripcion"],
                },
            )

        for role_name in perm["roles"]:
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
    op.drop_index("ix_instancia_encuentro_tenant_estado", table_name="instancia_encuentro")
    op.drop_index(op.f("ix_guardia_deleted_at"), table_name="guardia")
    op.drop_index(op.f("ix_guardia_cohorte_id"), table_name="guardia")
    op.drop_index(op.f("ix_guardia_carrera_id"), table_name="guardia")
    op.drop_index(op.f("ix_guardia_materia_id"), table_name="guardia")
    op.drop_index(op.f("ix_guardia_asignacion_id"), table_name="guardia")
    op.drop_index(op.f("ix_guardia_tenant_id"), table_name="guardia")
    op.drop_table("guardia")
    op.drop_index(
        op.f("ix_instancia_encuentro_deleted_at"), table_name="instancia_encuentro"
    )
    op.drop_index(op.f("ix_instancia_encuentro_fecha"), table_name="instancia_encuentro")
    op.drop_index(
        op.f("ix_instancia_encuentro_materia_id"), table_name="instancia_encuentro"
    )
    op.drop_index(
        op.f("ix_instancia_encuentro_slot_id"), table_name="instancia_encuentro"
    )
    op.drop_index(
        op.f("ix_instancia_encuentro_tenant_id"), table_name="instancia_encuentro"
    )
    op.drop_table("instancia_encuentro")
    op.drop_index(
        op.f("ix_slot_encuentro_deleted_at"), table_name="slot_encuentro"
    )
    op.drop_index(
        op.f("ix_slot_encuentro_materia_id"), table_name="slot_encuentro"
    )
    op.drop_index(
        op.f("ix_slot_encuentro_asignacion_id"), table_name="slot_encuentro"
    )
    op.drop_index(
        op.f("ix_slot_encuentro_tenant_id"), table_name="slot_encuentro"
    )
    op.drop_table("slot_encuentro")
