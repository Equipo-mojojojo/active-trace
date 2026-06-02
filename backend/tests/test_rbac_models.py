from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import create_test_tenant


@pytest.mark.asyncio
async def test_create_role(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    role = Role(tenant_id=tenant.id, nombre="PROFESOR", descripcion="Docente a cargo")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    assert role.id is not None
    assert isinstance(role.id, UUID)
    assert role.nombre == "PROFESOR"
    assert role.descripcion == "Docente a cargo"
    assert role.editable is True
    assert role.created_at is not None
    assert role.updated_at is not None
    assert role.deleted_at is None
    assert role.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_create_permission(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="calificaciones:importar",
        modulo="calificaciones",
        accion="importar",
        descripcion="Importar calificaciones desde padrones",
    )
    db_session.add(perm)
    await db_session.commit()
    await db_session.refresh(perm)

    assert perm.id is not None
    assert perm.codigo == "calificaciones:importar"
    assert perm.modulo == "calificaciones"
    assert perm.accion == "importar"


@pytest.mark.asyncio
async def test_create_role_permission(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    role = Role(tenant_id=tenant.id, nombre="PROFESOR")
    perm = Permission(
        tenant_id=tenant.id,
        codigo="calificaciones:importar:propio",
        modulo="calificaciones",
        accion="importar",
    )
    db_session.add_all([role, perm])
    await db_session.commit()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)
    await db_session.commit()
    await db_session.refresh(rp)

    assert rp.rol_id == role.id
    assert rp.permiso_id == perm.id
    assert rp.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_role_unique_name_per_tenant(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    role = Role(tenant_id=tenant.id, nombre="ADMIN")
    db_session.add(role)
    await db_session.commit()

    duplicate = Role(tenant_id=tenant.id, nombre="ADMIN")
    db_session.add(duplicate)
    with pytest.raises(Exception):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_permission_unique_code_per_tenant(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    perm1 = Permission(
        tenant_id=tenant.id,
        codigo="rbac:gestionar",
        modulo="rbac",
        accion="gestionar",
    )
    db_session.add(perm1)
    await db_session.commit()

    perm2 = Permission(
        tenant_id=tenant.id,
        codigo="rbac:gestionar",
        modulo="rbac",
        accion="gestionar",
    )
    db_session.add(perm2)
    with pytest.raises(Exception):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_role_unique_role_permission(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    role = Role(tenant_id=tenant.id, nombre="ADMIN")
    perm = Permission(
        tenant_id=tenant.id,
        codigo="rbac:gestionar",
        modulo="rbac",
        accion="gestionar",
    )
    db_session.add_all([role, perm])
    await db_session.commit()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp1 = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp1)
    await db_session.commit()

    rp2 = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp2)
    with pytest.raises(Exception):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_role_soft_delete(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session)
    role = Role(tenant_id=tenant.id, nombre="TUTOR")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    role.mark_deleted()
    await db_session.commit()
    await db_session.refresh(role)

    assert role.deleted_at is not None


@pytest.mark.asyncio
async def test_role_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await create_test_tenant(db_session, slug="tenant-a", name="Tenant A")
    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")

    role_a = Role(tenant_id=tenant_a.id, nombre="PROFESOR")
    role_b = Role(tenant_id=tenant_b.id, nombre="ALUMNO")
    db_session.add_all([role_a, role_b])
    await db_session.commit()

    result = await db_session.execute(
        select(Role).where(Role.tenant_id == tenant_a.id)
    )
    roles_a = result.scalars().all()

    assert len(roles_a) == 1
    assert roles_a[0].nombre == "PROFESOR"
    assert all(r.tenant_id == tenant_a.id for r in roles_a)


@pytest.mark.asyncio
async def test_permission_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await create_test_tenant(db_session, slug="tenant-a", name="Tenant A")
    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")

    perm_a = Permission(
        tenant_id=tenant_a.id,
        codigo="permiso:a",
        modulo="test",
        accion="a",
    )
    perm_b = Permission(
        tenant_id=tenant_b.id,
        codigo="permiso:b",
        modulo="test",
        accion="b",
    )
    db_session.add_all([perm_a, perm_b])
    await db_session.commit()

    result = await db_session.execute(
        select(Permission).where(Permission.tenant_id == tenant_a.id)
    )
    perms = result.scalars().all()

    assert len(perms) == 1
    assert perms[0].codigo == "permiso:a"
