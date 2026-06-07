"""create aviso and acknowledgment_aviso tables (C-15)

Revision ID: 0013_avisos_acknowledgment
Revises: 0012_evaluaciones_coloquios
Create Date: 2026-06-06 12:00:00

Creates tables:
- aviso (notificaciones con alcance configurable)
- acknowledgment_aviso (confirmación de lectura)

Seeds permissions:
- avisos:publicar
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0013_avisos_acknowledgment"
down_revision = "0012_evaluaciones_coloquios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- aviso ---
    op.create_table(
        "aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("alcance", sa.String(20), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("rol_destino", sa.String(50), nullable=True),
        sa.Column("severidad", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aviso_tenant_id"), "aviso", ["tenant_id"])
    op.create_index(op.f("ix_aviso_deleted_at"), "aviso", ["deleted_at"])

    # --- acknowledgment_aviso ---
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("aviso_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "usuario_id", name="uq_ack_aviso_usuario"),
    )
    op.create_index(op.f("ix_acknowledgment_aviso_tenant_id"), "acknowledgment_aviso", ["tenant_id"])
    op.create_index(op.f("ix_acknowledgment_aviso_aviso_id"), "acknowledgment_aviso", ["aviso_id"])
    op.create_index(op.f("ix_acknowledgment_aviso_usuario_id"), "acknowledgment_aviso", ["usuario_id"])
    op.create_index(op.f("ix_acknowledgment_aviso_deleted_at"), "acknowledgment_aviso", ["deleted_at"])

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
        ("avisos:publicar", "avisos", "publicar", "Publicar y gestionar avisos del sistema"),
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
            "avisos:publicar": ["COORDINADOR", "ADMIN"],
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
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
