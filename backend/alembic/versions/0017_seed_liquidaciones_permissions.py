"""seed liquidaciones y facturas permissions (C-18)

Revision ID: 0017_seed_liquidaciones_permissions
Revises: 0016_liquidaciones_honorarios
Create Date: 2026-06-06 21:30:00

No DDL — data seed only.
Seeds permissions: liquidaciones:ver, liquidaciones:cerrar,
liquidaciones:configurar-salarios, facturas:ver, facturas:gestionar.
Assigns to FINANZAS and ADMIN roles.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0017_seed_liquidaciones_permissions"
down_revision = "0016_liquidaciones_honorarios"
branch_labels = None
depends_on = None

PERMISSIONS = [
    ("liquidaciones:ver", "liquidaciones", "ver", "Ver liquidaciones de honorarios"),
    ("liquidaciones:cerrar", "liquidaciones", "cerrar", "Cerrar liquidación del período"),
    ("liquidaciones:configurar-salarios", "liquidaciones", "configurar-salarios", "ABM grilla salarial base y plus"),
    ("facturas:ver", "facturas", "ver", "Ver facturas de docentes que facturan"),
    ("facturas:gestionar", "facturas", "gestionar", "Crear y gestionar facturas"),
]

ROLE_PERMISSIONS = {
    "FINANZAS": ["liquidaciones:ver", "liquidaciones:cerrar", "liquidaciones:configurar-salarios", "facturas:ver", "facturas:gestionar"],
    "ADMIN": ["liquidaciones:ver", "facturas:ver"],
}


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return

    tid = str(row[0])

    perm_ids: dict[str, str] = {}
    for codigo, modulo, accion, descripcion in PERMISSIONS:
        existing = conn.execute(
            sa.text("SELECT id FROM permiso WHERE codigo = :c AND tenant_id = :t"),
            {"c": codigo, "t": tid},
        ).fetchone()
        if existing:
            perm_ids[codigo] = str(existing[0])
        else:
            pid = str(uuid4())
            conn.execute(
                sa.text(
                    "INSERT INTO permiso (id, tenant_id, codigo, modulo, accion, descripcion) "
                    "VALUES (:id, :t, :c, :m, :a, :d)"
                ),
                {"id": pid, "t": tid, "c": codigo, "m": modulo, "a": accion, "d": descripcion},
            )
            perm_ids[codigo] = pid

    for role_name, codigos in ROLE_PERMISSIONS.items():
        role_row = conn.execute(
            sa.text("SELECT id FROM rol WHERE nombre = :n AND tenant_id = :t"),
            {"n": role_name, "t": tid},
        ).fetchone()
        if role_row is None:
            continue
        rid = str(role_row[0])
        for codigo in codigos:
            pid = perm_ids.get(codigo)
            if pid is None:
                continue
            already = conn.execute(
                sa.text(
                    "SELECT id FROM rol_permiso WHERE rol_id = :r AND permiso_id = :p AND tenant_id = :t"
                ),
                {"r": rid, "p": pid, "t": tid},
            ).fetchone()
            if already:
                continue
            conn.execute(
                sa.text(
                    "INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id) VALUES (:id, :t, :r, :p)"
                ),
                {"id": str(uuid4()), "t": tid, "r": rid, "p": pid},
            )


def downgrade() -> None:
    pass
