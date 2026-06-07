"""seed auditoria:ver permission for FINANZAS role (C-19)

Revision ID: 0018_seed_auditoria_finanzas_permission
Revises: 0017_seed_liquidaciones_permissions
Create Date: 2026-06-06 22:00:00

No DDL — data seed only.
Ensures 'auditoria:ver' permission exists and assigns it to FINANZAS role.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0018_seed_auditoria_finanzas_permission"
down_revision = "0017_seed_liquidaciones_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return

    tid = str(row[0])

    existing = conn.execute(
        sa.text("SELECT id FROM permiso WHERE codigo = 'auditoria:ver' AND tenant_id = :t"),
        {"t": tid},
    ).fetchone()

    if existing:
        perm_id = str(existing[0])
    else:
        perm_id = str(uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO permiso (id, tenant_id, codigo, modulo, accion, descripcion) "
                "VALUES (:id, :t, 'auditoria:ver', 'auditoria', 'ver', "
                "'Ver panel de auditoría y métricas de uso')"
            ),
            {"id": perm_id, "t": tid},
        )

    role_row = conn.execute(
        sa.text("SELECT id FROM rol WHERE nombre = 'FINANZAS' AND tenant_id = :t"),
        {"t": tid},
    ).fetchone()

    if role_row is None:
        return

    rid = str(role_row[0])

    already = conn.execute(
        sa.text(
            "SELECT id FROM rol_permiso WHERE rol_id = :r AND permiso_id = :p AND tenant_id = :t"
        ),
        {"r": rid, "p": perm_id, "t": tid},
    ).fetchone()

    if already:
        return

    conn.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id) "
            "VALUES (:id, :t, :r, :p)"
        ),
        {"id": str(uuid4()), "t": tid, "r": rid, "p": perm_id},
    )


def downgrade() -> None:
    pass
