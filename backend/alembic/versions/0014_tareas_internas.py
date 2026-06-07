"""create tarea and comentario_tarea tables (C-16)

Revision ID: 0014_tareas_internas
Revises: 0013_avisos_acknowledgment
Create Date: 2026-06-06 14:00:00

Creates tables:
- tarea (internal tasks with assignee, status, optional context)
- comentario_tarea (threaded comments on tasks)

Seeds permissions:
- tareas:gestionar
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0014_tareas_internas"
down_revision = "0013_avisos_acknowledgment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- tarea ---
    op.create_table(
        "tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("asignado_a", sa.Uuid(), nullable=False),
        sa.Column("asignado_por", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["asignado_a"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["asignado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tarea_tenant_id"), "tarea", ["tenant_id"])
    op.create_index(op.f("ix_tarea_deleted_at"), "tarea", ["deleted_at"])
    op.create_index(op.f("ix_tarea_asignado_a"), "tarea", ["asignado_a"])

    # --- comentario_tarea ---
    op.create_table(
        "comentario_tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("tarea_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("creado_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["tarea_id"], ["tarea.id"]),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comentario_tarea_tenant_id"), "comentario_tarea", ["tenant_id"])
    op.create_index(op.f("ix_comentario_tarea_tarea_id"), "comentario_tarea", ["tarea_id"])
    op.create_index(op.f("ix_comentario_tarea_deleted_at"), "comentario_tarea", ["deleted_at"])

    # --- Seed permissions ---
    _seed_permissions(op.get_bind())


def _seed_permissions(conn) -> None:
    tenant_t = sa.table("tenant", sa.Column("id", sa.Uuid()))
    permiso_t = sa.table(
        "permiso",
        sa.Column("id", sa.Uuid()),
        sa.Column("tenant_id", sa.Uuid()),
        sa.Column("codigo", sa.String(100)),
        sa.Column("modulo", sa.String(50)),
        sa.Column("accion", sa.String(50)),
        sa.Column("descripcion", sa.String(255)),
    )
    role_t = sa.table(
        "rol",
        sa.Column("id", sa.Uuid()),
        sa.Column("tenant_id", sa.Uuid()),
        sa.Column("nombre", sa.String(100)),
    )
    rp_t = sa.table(
        "rol_permiso",
        sa.Column("id", sa.Uuid()),
        sa.Column("tenant_id", sa.Uuid()),
        sa.Column("rol_id", sa.Uuid()),
        sa.Column("permiso_id", sa.Uuid()),
    )

    tenants = conn.execute(sa.select(tenant_t.c.id)).fetchall()
    if not tenants:
        return

    perms_data = [
        ("tareas:gestionar", "tareas", "gestionar", "Gestionar tareas internas"),
    ]

    for tenant in tenants:
        tid = tenant[0]

        perm_ids = {}
        for codigo, modulo, accion, desc in perms_data:
            existing = conn.execute(
                sa.select(permiso_t.c.id).where(
                    permiso_t.c.tenant_id == tid,
                    permiso_t.c.codigo == codigo,
                )
            ).fetchone()

            if existing:
                perm_ids[codigo] = existing[0]
            else:
                perm_id = uuid4()
                conn.execute(
                    sa.insert(permiso_t).values(
                        id=perm_id,
                        tenant_id=tid,
                        codigo=codigo,
                        modulo=modulo,
                        accion=accion,
                        descripcion=desc,
                    )
                )
                perm_ids[codigo] = perm_id

        roles = conn.execute(
            sa.select(role_t.c.id, role_t.c.nombre).where(role_t.c.tenant_id == tid)
        ).fetchall()
        role_map = {r.nombre: r.id for r in roles}

        assigned_roles = {
            "tareas:gestionar": ["COORDINADOR", "ADMIN"],
        }

        for codigo, role_names in assigned_roles.items():
            perm_id = perm_ids.get(codigo)
            if not perm_id:
                continue

            for role_name in role_names:
                role_id = role_map.get(role_name)
                if not role_id:
                    continue

                already = conn.execute(
                    sa.select(rp_t.c.id).where(
                        rp_t.c.tenant_id == tid,
                        rp_t.c.rol_id == role_id,
                        rp_t.c.permiso_id == perm_id,
                    )
                ).fetchone()

                if already:
                    continue

                conn.execute(
                    sa.insert(rp_t).values(
                        id=uuid4(),
                        tenant_id=tid,
                        rol_id=role_id,
                        permiso_id=perm_id,
                    )
                )


def downgrade() -> None:
    op.drop_table("comentario_tarea")
    op.drop_table("tarea")
