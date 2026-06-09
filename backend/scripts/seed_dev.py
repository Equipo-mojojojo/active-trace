"""
Seed script for local development.

Creates:
  - 1 demo tenant  (slug="demo", name="Instituto Demo")
  - All 7 roles + 30 permissions from the RBAC matrix (migration 0003 data)
  - 1 ADMIN user   (email="admin@demo.com", password="Admin1234!")
  - 1 Usuario      (nombre="Admin", apellidos="Demo")

Idempotent: skips any object that already exists (by slug / email lookup).

Usage (from backend/ directory):
    python -m scripts.seed_dev
OR (from anywhere):
    python backend/scripts/seed_dev.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ensure the backend root is on the path so app imports work
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import build_email_lookup, hash_password
from app.models.base import BaseModelMixin  # noqa: F401 — ensure mappers are registered
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User

# ---------------------------------------------------------------------------
# RBAC data (mirrors alembic/versions/0003_create_rbac_tables.py)
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

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ALUMNO": ["propio:ver_estado", "evaluacion:reservar", "aviso:ack"],
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
    "NEXO": ["aviso:ack", "comunicacion:enviar", "atrasados:ver"],
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

_ROLE_DESCRIPTIONS = {
    "ALUMNO": "Estudiante que cursa materias",
    "TUTOR": "Auxiliar o ayudante de cátedra",
    "PROFESOR": "Docente a cargo de una o más comisiones",
    "COORDINADOR": "Responsable de conjunto de materias o cohorte",
    "NEXO": "Rol de articulación y enlace transversal",
    "ADMIN": "Administrador del sistema dentro del tenant",
    "FINANZAS": "Responsable de liquidaciones y honorarios",
}

# ---------------------------------------------------------------------------
# Dev credentials
# ---------------------------------------------------------------------------

DEV_EMAIL = "admin@demo.com"
DEV_PASSWORD = "Admin1234!"
DEV_TENANT_SLUG = "demo"
DEV_TENANT_NAME = "Instituto Demo"

DEV_USERS = [
    {"email": "admin@demo.com",       "password": "Admin1234!",   "full_name": "Admin Demo",        "roles": ["ADMIN"]},
    {"email": "profesor@demo.com",    "password": "Profesor1234!", "full_name": "Profesor Demo",     "roles": ["PROFESOR"]},
    {"email": "coordinador@demo.com", "password": "Coord1234!",   "full_name": "Coordinador Demo",  "roles": ["COORDINADOR"]},
    {"email": "finanzas@demo.com",    "password": "Finanzas1234!", "full_name": "Finanzas Demo",    "roles": ["FINANZAS"]},
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


async def seed(session: AsyncSession) -> None:
    # ── 1. Tenant ────────────────────────────────────────────────────────────
    existing_tenant = await session.scalar(
        select(Tenant).where(Tenant.slug == DEV_TENANT_SLUG)
    )
    if existing_tenant:
        print(f"  [skip] Tenant '{DEV_TENANT_SLUG}' already exists")
        tenant = existing_tenant
    else:
        tenant = Tenant(slug=DEV_TENANT_SLUG, name=DEV_TENANT_NAME)
        session.add(tenant)
        await session.flush()
        print(f"  [ok]   Tenant '{DEV_TENANT_SLUG}' created  id={tenant.id}")

    tenant_id = tenant.id

    # ── 2. Permissions ───────────────────────────────────────────────────────
    existing_perm_codes = set(
        await session.scalars(
            select(Permission.codigo).where(Permission.tenant_id == tenant_id)
        )
    )

    perm_id_by_code: dict[str, object] = {}

    # Load existing permission IDs first
    if existing_perm_codes:
        rows = await session.execute(
            select(Permission.codigo, Permission.id).where(
                Permission.tenant_id == tenant_id
            )
        )
        for codigo, pid in rows:
            perm_id_by_code[codigo] = pid

    created_perm_count = 0
    for codigo, modulo, accion, descripcion in _PERMISSIONS:
        if codigo in existing_perm_codes:
            continue
        perm = Permission(
            tenant_id=tenant_id,
            codigo=codigo,
            modulo=modulo,
            accion=accion,
            descripcion=descripcion,
        )
        session.add(perm)
        await session.flush()
        perm_id_by_code[codigo] = perm.id
        created_perm_count += 1

    if created_perm_count:
        print(f"  [ok]   {created_perm_count} permissions created")
    else:
        print(f"  [skip] Permissions already exist ({len(existing_perm_codes)} found)")

    # ── 3. Roles + role-permission links ─────────────────────────────────────
    existing_role_names = set(
        await session.scalars(
            select(Role.nombre).where(Role.tenant_id == tenant_id)
        )
    )

    created_role_count = 0
    for role_name, perm_codes in _ROLE_PERMISSIONS.items():
        if role_name in existing_role_names:
            continue

        role = Role(
            tenant_id=tenant_id,
            nombre=role_name,
            descripcion=_ROLE_DESCRIPTIONS.get(role_name, ""),
            editable=role_name != "ADMIN",
        )
        session.add(role)
        await session.flush()

        for perm_code in perm_codes:
            perm_id = perm_id_by_code.get(perm_code)
            if perm_id is None:
                print(f"  [warn] Unknown permission code '{perm_code}' — skipped")
                continue
            rp = RolePermission(
                tenant_id=tenant_id,
                rol_id=role.id,
                permiso_id=perm_id,
            )
            session.add(rp)

        await session.flush()
        created_role_count += 1

    if created_role_count:
        print(f"  [ok]   {created_role_count} roles created")
    else:
        print(f"  [skip] Roles already exist ({len(existing_role_names)} found)")

    # ── 4. User accounts ─────────────────────────────────────────────────────
    for dev_user in DEV_USERS:
        email_lookup = build_email_lookup(dev_user["email"])
        existing_user = await session.scalar(
            select(User).where(User.email_lookup == email_lookup)
        )
        if existing_user:
            print(f"  [skip] User '{dev_user['email']}' already exists")
        else:
            user = User(
                tenant_id=tenant_id,
                email=dev_user["email"],
                email_lookup=email_lookup,
                full_name=dev_user["full_name"],
                password_hash=hash_password(dev_user["password"]),
                roles=dev_user["roles"],
                is_active=True,
                two_factor_enabled=False,
            )
            session.add(user)
            await session.flush()
            print(f"  [ok]   User '{dev_user['email']}' created  id={user.id}")

    await session.commit()


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    print("\n=== activia-trace dev seed ===")
    async with async_session() as session:
        try:
            await seed(session)
        except Exception:
            await session.rollback()
            raise
    await engine.dispose()
    print("\nDone. Dev credentials:")
    for u in DEV_USERS:
        print(f"  [{u['roles'][0]:<12}]  {u['email']:<28}  /  {u['password']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
