"""seed atrasados:ver permission (C-11)

Revision ID: 0009_seed_atrasados_permission
Revises: 0008_create_calificacion_umbral_tables
Create Date: 2026-06-04 12:00:00

No DDL changes — only data seed.
Seeds the 'atrasados:ver' permission and assigns it to
TUTOR, PROFESOR, COORDINADOR, and ADMIN roles.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0009_seed_atrasados_permission"
down_revision = "0008_calificacion_umbral"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return

    default_tenant_id = str(row[0])

    existing = conn.execute(
        sa.text(
            "SELECT id FROM permiso WHERE codigo = 'atrasados:ver' AND tenant_id = :tid"
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
                "codigo": "atrasados:ver",
                "modulo": "atrasados",
                "accion": "ver",
                "descripcion": "Ver alumnos atrasados, ranking y reportes académicos",
            },
        )

    for role_name in ("TUTOR", "PROFESOR", "COORDINADOR", "ADMIN"):
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
    # Data-only migration — downgrade is a no-op to avoid data loss
    pass
