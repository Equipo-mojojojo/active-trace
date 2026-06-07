"""create evaluacion and coloquio tables (C-14)

Revision ID: 0012_evaluaciones_coloquios
Revises: 0011_encuentros_guardias
Create Date: 2026-06-06 11:30:00

Creates tables:
- evaluacion (convocatoria de coloquio)
- turno_evaluacion (turnos con cupo)
- convocado (alumnos habilitados)
- reserva_evaluacion (turnos reservados)
- resultado_evaluacion (notas finales)

Seeds permissions:
- coloquios:gestionar, coloquios:reservar, coloquios:ver
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0012_evaluaciones_coloquios"
down_revision = "0011_encuentros_guardias"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- evaluacion ---
    op.create_table(
        "evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("instancia", sa.String(255), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Abierta"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluacion_tenant_id"), "evaluacion", ["tenant_id"])
    op.create_index(op.f("ix_evaluacion_materia_id"), "evaluacion", ["materia_id"])
    op.create_index(op.f("ix_evaluacion_cohorte_id"), "evaluacion", ["cohorte_id"])
    op.create_index(op.f("ix_evaluacion_deleted_at"), "evaluacion", ["deleted_at"])

    # --- turno_evaluacion ---
    op.create_table(
        "turno_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("max_cupo", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_turno_evaluacion_tenant_id"), "turno_evaluacion", ["tenant_id"])
    op.create_index(op.f("ix_turno_evaluacion_evaluacion_id"), "turno_evaluacion", ["evaluacion_id"])
    op.create_index(op.f("ix_turno_evaluacion_deleted_at"), "turno_evaluacion", ["deleted_at"])

    # --- convocado ---
    op.create_table(
        "convocado",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluacion_id", "alumno_id", name="uq_convocado_evaluacion_alumno"),
    )
    op.create_index(op.f("ix_convocado_tenant_id"), "convocado", ["tenant_id"])
    op.create_index(op.f("ix_convocado_evaluacion_id"), "convocado", ["evaluacion_id"])
    op.create_index(op.f("ix_convocado_alumno_id"), "convocado", ["alumno_id"])
    op.create_index(op.f("ix_convocado_deleted_at"), "convocado", ["deleted_at"])

    # --- reserva_evaluacion ---
    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("turno_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["turno_id"], ["turno_evaluacion.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reserva_evaluacion_tenant_id"), "reserva_evaluacion", ["tenant_id"])
    op.create_index(op.f("ix_reserva_evaluacion_turno_id"), "reserva_evaluacion", ["turno_id"])
    op.create_index(op.f("ix_reserva_evaluacion_alumno_id"), "reserva_evaluacion", ["alumno_id"])
    op.create_index(op.f("ix_reserva_evaluacion_deleted_at"), "reserva_evaluacion", ["deleted_at"])

    # --- resultado_evaluacion ---
    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("nota_final", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resultado_evaluacion_tenant_id"), "resultado_evaluacion", ["tenant_id"])
    op.create_index(op.f("ix_resultado_evaluacion_evaluacion_id"), "resultado_evaluacion", ["evaluacion_id"])
    op.create_index(op.f("ix_resultado_evaluacion_alumno_id"), "resultado_evaluacion", ["alumno_id"])
    op.create_index(op.f("ix_resultado_evaluacion_deleted_at"), "resultado_evaluacion", ["deleted_at"])

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
        ("coloquios:gestionar", "coloquios", "gestionar", "Gestionar convocatorias de coloquio"),
        ("coloquios:reservar", "coloquios", "reservar", "Reservar turno de coloquio"),
        ("coloquios:ver", "coloquios", "ver", "Ver convocatorias y métricas de coloquios"),
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
            "coloquios:gestionar": ["COORDINADOR", "ADMIN"],
            "coloquios:ver": ["COORDINADOR", "ADMIN"],
            "coloquios:reservar": ["ALUMNO"],
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
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("convocado")
    op.drop_table("turno_evaluacion")
    op.drop_table("evaluacion")
