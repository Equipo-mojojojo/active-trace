"""create RBAC tables (role, permission, role_permission) + seed data

Revision ID: 0003_create_rbac_tables
Revises: 0002_create_auth_tables
Create Date: 2026-06-02 16:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

revision = "0003_create_rbac_tables"
down_revision = "0002_create_auth_tables"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Permission matrix from knowledge-base/03_actores_y_roles.md §3.3
# Each entry: (codigo, modulo, accion, descripcion)
# ---------------------------------------------------------------------------

_PERMISSIONS = [
    ("propio:ver_estado", "propio", "ver_estado", "Ver estado académico propio"),
    ("evaluacion:reservar", "evaluacion", "reservar", "Reservar instancia de evaluación"),
    ("aviso:ack", "aviso", "ack", "Confirmar avisos (acknowledgment)"),
    ("calificaciones:importar", "calificaciones", "importar", "Importar calificaciones de cualquier comisión"),
    ("calificaciones:importar:propio", "calificaciones", "importar", "Importar calificaciones de comisiones propias"),
    ("atrasados:ver", "atrasados", "ver", "Ver alumnos atrasados de cualquier comisión"),
    ("atrasados:ver:propio", "atrasados", "ver", "Ver alumnos atrasados de comisiones propias"),
    ("entregas:ver_sin_corregir", "entregas", "ver_sin_corregir", "Ver entregas sin corregir de cualquier comisión"),
    ("entregas:ver_sin_corregir:propio", "entregas", "ver_sin_corregir", "Ver entregas sin corregir de comisiones propias"),
    ("comunicacion:enviar", "comunicacion", "enviar", "Enviar comunicaciones a cualquier grupo"),
    ("comunicacion:enviar:propio", "comunicacion", "enviar", "Enviar comunicaciones a alumnos propios"),
    ("comunicacion:aprobar", "comunicacion", "aprobar", "Aprobar comunicaciones masivas"),
    ("encuentros:gestionar", "encuentros", "gestionar", "Gestionar encuentros de cualquier comisión"),
    ("encuentros:gestionar:propio", "encuentros", "gestionar", "Gestionar encuentros de comisiones propias"),
    ("guardias:registrar", "guardias", "registrar", "Registrar guardias de cualquier turno"),
    ("guardias:registrar:propio", "guardias", "registrar", "Registrar guardias propias"),
    ("tareas:gestionar", "tareas", "gestionar", "Gestionar tareas internas de cualquier equipo"),
    ("tareas:gestionar:propio", "tareas", "gestionar", "Gestionar tareas internas propias"),
    ("avisos:publicar", "avisos", "publicar", "Publicar avisos institucionales"),
    ("equipos:asignar", "equipos", "asignar", "Gestionar equipos docentes y asignaciones"),
    ("estructura:gestionar", "estructura", "gestionar", "Gestionar carrera, cohortes, materias"),
    ("usuarios:gestionar", "usuarios", "gestionar", "Gestionar usuarios del tenant"),
    ("auditoria:ver", "auditoria", "ver", "Ver registro de auditoría completo"),
    ("auditoria:ver:propio", "auditoria", "ver", "Ver registro de auditoría de acciones propias"),
    ("liquidaciones:operar", "liquidaciones", "operar", "Operar grilla salarial"),
    ("liquidaciones:cerrar", "liquidaciones", "cerrar", "Calcular y cerrar liquidaciones"),
    ("facturas:gestionar", "facturas", "gestionar", "Gestionar facturas"),
    ("tenant:configurar", "tenant", "configurar", "Configurar parámetros del tenant"),
    ("rbac:gestionar", "rbac", "gestionar", "Gestionar roles y permisos del tenant"),
    ("impersonacion:usar", "impersonacion", "usar", "Usar impersonación para soporte"),
]

# Role → [perm_codes]
_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ALUMNO": [
        "propio:ver_estado",
        "evaluacion:reservar",
        "aviso:ack",
    ],
    "TUTOR": [
        "aviso:ack",
        "atrasados:ver:propio",
        "entregas:ver_sin_corregir:propio",
        "encuentros:gestionar:propio",
        "guardias:registrar:propio",
    ],
    "PROFESOR": [
        "aviso:ack",
        "calificaciones:importar:propio",
        "atrasados:ver:propio",
        "entregas:ver_sin_corregir:propio",
        "comunicacion:enviar:propio",
        "encuentros:gestionar:propio",
        "guardias:registrar:propio",
        "tareas:gestionar:propio",
    ],
    "COORDINADOR": [
        "aviso:ack",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "auditoria:ver:propio",
    ],
    "NEXO": [
        "aviso:ack",
        "comunicacion:enviar",
        "atrasados:ver",
    ],
    "ADMIN": [
        "aviso:ack",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "estructura:gestionar",
        "usuarios:gestionar",
        "auditoria:ver",
        "tenant:configurar",
        "rbac:gestionar",
        "impersonacion:usar",
    ],
    "FINANZAS": [
        "aviso:ack",
        "auditoria:ver",
        "liquidaciones:operar",
        "liquidaciones:cerrar",
        "facturas:gestionar",
    ],
}


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # rol
    # -----------------------------------------------------------------------
    op.create_table(
        "rol",
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("editable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "nombre", name="uq_rol_tenant_nombre"),
    )
    op.create_index(op.f("ix_rol_deleted_at"), "rol", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_rol_tenant_id"), "rol", ["tenant_id"], unique=False)

    # -----------------------------------------------------------------------
    # permiso
    # -----------------------------------------------------------------------
    op.create_table(
        "permiso",
        sa.Column("codigo", sa.String(length=100), nullable=False),
        sa.Column("modulo", sa.String(length=50), nullable=False),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_permiso_tenant_codigo"),
    )
    op.create_index(op.f("ix_permiso_deleted_at"), "permiso", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_permiso_tenant_id"), "permiso", ["tenant_id"], unique=False)

    # -----------------------------------------------------------------------
    # rol_permiso
    # -----------------------------------------------------------------------
    op.create_table(
        "rol_permiso",
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.Column("permiso_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["rol_id"], ["rol.id"]),
        sa.ForeignKeyConstraint(["permiso_id"], ["permiso.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rol_id", "permiso_id", "tenant_id", name="uq_rol_permiso_tenant"
        ),
    )
    op.create_index(
        op.f("ix_rol_permiso_deleted_at"), "rol_permiso", ["deleted_at"], unique=False
    )
    op.create_index(
        op.f("ix_rol_permiso_tenant_id"), "rol_permiso", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_rol_permiso_rol_id"), "rol_permiso", ["rol_id"], unique=False
    )
    op.create_index(
        op.f("ix_rol_permiso_permiso_id"), "rol_permiso", ["permiso_id"], unique=False
    )

    # -----------------------------------------------------------------------
    # Seed data — permission catalog + roles
    #
    # NOTE: This seeds permissions into the DEFAULT tenant. In production,
    # the tenant table should have at least one tenant before running this.
    # For multi-tenant setups, seeding is handled per-tenant on creation.
    # -----------------------------------------------------------------------
    conn = op.get_bind()

    # Seed only if a tenant already exists — skip on fresh DB installs
    result = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1"))
    row = result.fetchone()
    if row is None:
        return
    default_tenant_id = str(row[0])

    # Build a lookup map: perm_code → perm_id (will be populated after insert)
    perm_id_by_code: dict[str, str] = {}

    for codigo, modulo, accion, descripcion in _PERMISSIONS:
        perm_id = str(uuid4())
        perm_id_by_code[codigo] = perm_id
        conn.execute(
            sa.text(
                """INSERT INTO permiso (id, tenant_id, codigo, modulo, accion, descripcion)
                   VALUES (:id, :tenant_id, :codigo, :modulo, :accion, :descripcion)"""
            ),
            {
                "id": perm_id,
                "tenant_id": default_tenant_id,
                "codigo": codigo,
                "modulo": modulo,
                "accion": accion,
                "descripcion": descripcion,
            },
        )

    # Create seed roles and assign permissions
    for role_name, perm_codes in _ROLE_PERMISSIONS.items():
        role_id = str(uuid4())
        descripcion_map = {
            "ALUMNO": "Estudiante que cursa materias",
            "TUTOR": "Auxiliar o ayudante de cátedra",
            "PROFESOR": "Docente a cargo de una o más comisiones",
            "COORDINADOR": "Responsable de conjunto de materias o cohorte",
            "NEXO": "Rol de articulación y enlace transversal",
            "ADMIN": "Administrador del sistema dentro del tenant",
            "FINANZAS": "Responsable de liquidaciones y honorarios",
        }
        conn.execute(
            sa.text(
                """INSERT INTO rol (id, tenant_id, nombre, descripcion, editable)
                   VALUES (:id, :tenant_id, :nombre, :descripcion, :editable)"""
            ),
            {
                "id": role_id,
                "tenant_id": default_tenant_id,
                "nombre": role_name,
                "descripcion": descripcion_map.get(role_name, ""),
                "editable": role_name not in ("ADMIN",),
            },
        )

        for perm_code in perm_codes:
            perm_id = perm_id_by_code.get(perm_code)
            if perm_id is None:
                continue

            rp_id = str(uuid4())
            conn.execute(
                sa.text(
                    """INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id)
                       VALUES (:id, :tenant_id, :rol_id, :permiso_id)"""
                ),
                {
                    "id": rp_id,
                    "tenant_id": default_tenant_id,
                    "rol_id": role_id,
                    "permiso_id": perm_id,
                },
            )


def downgrade() -> None:
    op.drop_index(op.f("ix_rol_permiso_permiso_id"), table_name="rol_permiso")
    op.drop_index(op.f("ix_rol_permiso_rol_id"), table_name="rol_permiso")
    op.drop_index(op.f("ix_rol_permiso_tenant_id"), table_name="rol_permiso")
    op.drop_index(op.f("ix_rol_permiso_deleted_at"), table_name="rol_permiso")
    op.drop_table("rol_permiso")

    op.drop_index(op.f("ix_permiso_tenant_id"), table_name="permiso")
    op.drop_index(op.f("ix_permiso_deleted_at"), table_name="permiso")
    op.drop_table("permiso")

    op.drop_index(op.f("ix_rol_tenant_id"), table_name="rol")
    op.drop_index(op.f("ix_rol_deleted_at"), table_name="rol")
    op.drop_table("rol")
