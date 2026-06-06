from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    _perm_base_code,
    _perm_is_global,
    _perm_propio_code,
    clear_all_caches,
    get_cached_permissions,
    get_effective_permissions,
    has_permission_with_scope,
    invalidate_permission_cache,
    invalidate_permission_cache_for_role,
    set_cached_permissions,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import create_test_tenant, create_test_user

# ---------------------------------------------------------------------------
# Helpers para construir datos de prueba RBAC
# ---------------------------------------------------------------------------


async def _seed_role_with_perms(
    db_session: AsyncSession,
    tenant_id: UUID,
    nombre: str,
    perm_codes: list[list[str]],
) -> Role:
    """Create a role and assign permissions from a list of [codigo, modulo, accion]."""
    role = Role(tenant_id=tenant_id, nombre=nombre)
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)

    for codigo, modulo, accion in perm_codes:
        perm = Permission(
            tenant_id=tenant_id,
            codigo=codigo,
            modulo=modulo,
            accion=accion,
        )
        db_session.add(perm)
        await db_session.flush()
        await db_session.refresh(perm)

        rp = RolePermission(tenant_id=tenant_id, rol_id=role.id, permiso_id=perm.id)
        db_session.add(rp)

    await db_session.commit()
    return role


# ===================================================================
# 3.3 — Permission Resolution Tests
# ===================================================================


@pytest.mark.asyncio
async def test_get_effective_permissions_multi_role_union(db_session: AsyncSession) -> None:
    """User with multiple roles gets the union of all permissions."""
    tenant = await create_test_tenant(db_session)

    await _seed_role_with_perms(
        db_session, tenant.id, "PROFESOR",
        [
            ["calificaciones:importar:propio", "calificaciones", "importar"],
            ["atrasados:ver:propio", "atrasados", "ver"],
        ],
    )
    await _seed_role_with_perms(
        db_session, tenant.id, "COORDINADOR",
        [
            ["calificaciones:importar", "calificaciones", "importar"],
            ["atrasados:ver", "atrasados", "ver"],
            ["avisos:publicar", "avisos", "publicar"],
        ],
    )

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="profesor@test.com",
        roles=["PROFESOR", "COORDINADOR"],
    )

    perms = await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=False,
    )

    assert perms == {
        "calificaciones:importar:propio",
        "atrasados:ver:propio",
        "calificaciones:importar",
        "atrasados:ver",
        "avisos:publicar",
    }


@pytest.mark.asyncio
async def test_get_effective_permissions_no_roles(db_session: AsyncSession) -> None:
    """User with no roles gets empty permission set."""
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="noroles@test.com", roles=[],
    )

    perms = await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=False,
    )

    assert perms == set()


@pytest.mark.asyncio
async def test_get_effective_permissions_unknown_user(db_session: AsyncSession) -> None:
    """Non-existent user returns empty set."""
    tenant = await create_test_tenant(db_session)
    fake_id = UUID("00000000-0000-0000-0000-000000000001")

    perms = await get_effective_permissions(
        user_id=fake_id, tenant_id=tenant.id, db=db_session, use_cache=False,
    )

    assert perms == set()


@pytest.mark.asyncio
async def test_get_effective_permissions_tenant_isolation(db_session: AsyncSession) -> None:
    """Permissions from tenant B do not leak into tenant A."""
    tenant_a = await create_test_tenant(db_session, slug="tenant-a", name="Tenant A")
    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")

    await _seed_role_with_perms(
        db_session, tenant_b.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )

    user_a = await create_test_user(
        db_session, tenant_id=tenant_a.id, email="a@test.com", roles=["ADMIN"],
    )

    perms = await get_effective_permissions(
        user_id=user_a.id, tenant_id=tenant_a.id, db=db_session, use_cache=False,
    )

    assert perms == set()


# ===================================================================
# 3.4 — Cache Tests
# ===================================================================


@pytest.mark.asyncio
async def test_cache_miss_then_hit(db_session: AsyncSession) -> None:
    """First call populates cache, second call hits it."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="cache@test.com", roles=["ADMIN"],
    )

    # Primera llamada — cache miss, consulta DB
    perms1 = await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=True,
    )

    cached = get_cached_permissions(tenant.id, user.id)
    assert cached is not None
    assert cached == perms1

    # Segunda llamada — debe usar cache (no podemos probar que no fue a DB
    # sin mock, pero verificamos que devuelve lo mismo)
    perms2 = await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=True,
    )
    assert perms2 == perms1


@pytest.mark.asyncio
async def test_cache_bypass_with_use_cache_false(db_session: AsyncSession) -> None:
    """use_cache=False does not populate the cache."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="nocache@test.com", roles=["ADMIN"],
    )

    await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=False,
    )

    cached = get_cached_permissions(tenant.id, user.id)
    assert cached is None


@pytest.mark.asyncio
async def test_cache_invalidate_by_user(db_session: AsyncSession) -> None:
    """Invalidate cache for a specific user."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="inval@test.com", roles=["ADMIN"],
    )

    await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=True,
    )
    assert get_cached_permissions(tenant.id, user.id) is not None

    invalidate_permission_cache(tenant_id=tenant.id, user_id=user.id)
    assert get_cached_permissions(tenant.id, user.id) is None


@pytest.mark.asyncio
async def test_cache_invalidate_by_tenant(db_session: AsyncSession) -> None:
    """Invalidate cache for all users in a tenant."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user1 = await create_test_user(
        db_session, tenant_id=tenant.id, email="u1@test.com", roles=["ADMIN"],
    )
    user2 = await create_test_user(
        db_session, tenant_id=tenant.id, email="u2@test.com", roles=["ADMIN"],
    )

    for u in [user1, user2]:
        await get_effective_permissions(
            user_id=u.id, tenant_id=tenant.id, db=db_session, use_cache=True,
        )
        assert get_cached_permissions(tenant.id, u.id) is not None

    # Invalidar todo el tenant
    invalidate_permission_cache(tenant_id=tenant.id)

    for u in [user1, user2]:
        assert get_cached_permissions(tenant.id, u.id) is None


@pytest.mark.asyncio
async def test_cache_invalidate_by_role(db_session: AsyncSession) -> None:
    """invalidate_permission_cache_for_role invalidates all entries for tenant."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="roleinv@test.com", roles=["ADMIN"],
    )

    await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=True,
    )
    assert get_cached_permissions(tenant.id, user.id) is not None

    invalidate_permission_cache_for_role(tenant.id, "ADMIN")
    assert get_cached_permissions(tenant.id, user.id) is None


@pytest.mark.asyncio
async def test_cache_clear_all(db_session: AsyncSession) -> None:
    """clear_all_caches() empties everything."""
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="clear@test.com", roles=["ADMIN"],
    )

    await get_effective_permissions(
        user_id=user.id, tenant_id=tenant.id, db=db_session, use_cache=True,
    )
    assert get_cached_permissions(tenant.id, user.id) is not None

    clear_all_caches()
    assert get_cached_permissions(tenant.id, user.id) is None


@pytest.mark.asyncio
async def test_cache_isolation_between_tenants(db_session: AsyncSession) -> None:
    """Cache entries for different tenants do not interfere."""
    clear_all_caches()
    tenant_a = await create_test_tenant(db_session, slug="tenant-a", name="Tenant A")
    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")

    await _seed_role_with_perms(
        db_session, tenant_a.id, "ADMIN",
        [["rbac:gestionar", "rbac", "gestionar"]],
    )

    user_a = await create_test_user(
        db_session, tenant_id=tenant_a.id, email="a@test.com", roles=["ADMIN"],
    )

    await get_effective_permissions(
        user_id=user_a.id, tenant_id=tenant_a.id, db=db_session, use_cache=True,
    )

    assert get_cached_permissions(tenant_a.id, user_a.id) is not None
    # Should not exist under tenant_b key
    assert get_cached_permissions(tenant_b.id, user_a.id) is None


# ===================================================================
# 5.3 — Scoping Tests
# ===================================================================


@pytest.mark.asyncio
async def test_scoping_global_perm_passes(db_session: AsyncSession) -> None:
    """Global permission passes regardless of resource_owner_id."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ADMIN",
        [["calificaciones:importar", "calificaciones", "importar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="global@test.com", roles=["ADMIN"],
    )

    different_owner = UUID("00000000-0000-0000-0000-000000000999")
    result = await has_permission_with_scope(
        permiso_base="calificaciones:importar",
        user=user,
        resource_owner_id=different_owner,
        db=db_session,
        use_cache=False,
    )

    assert result is True


@pytest.mark.asyncio
async def test_scoping_propio_owner_passes(db_session: AsyncSession) -> None:
    """:propio permission passes when resource_owner_id == user.id."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "PROFESOR",
        [["calificaciones:importar:propio", "calificaciones", "importar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="propio@test.com", roles=["PROFESOR"],
    )

    result = await has_permission_with_scope(
        permiso_base="calificaciones:importar",
        user=user,
        resource_owner_id=user.id,
        db=db_session,
        use_cache=False,
    )

    assert result is True


@pytest.mark.asyncio
async def test_scoping_propio_not_owner_fails(db_session: AsyncSession) -> None:
    """:propio permission fails when resource_owner_id != user.id."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "PROFESOR",
        [["calificaciones:importar:propio", "calificaciones", "importar"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="notowner@test.com", roles=["PROFESOR"],
    )

    result = await has_permission_with_scope(
        permiso_base="calificaciones:importar",
        user=user,
        resource_owner_id=UUID("00000000-0000-0000-0000-000000000999"),
        db=db_session,
        use_cache=False,
    )

    assert result is False


@pytest.mark.asyncio
async def test_scoping_no_permission_fails(db_session: AsyncSession) -> None:
    """User without any variant of the permission returns False."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    await _seed_role_with_perms(
        db_session, tenant.id, "ALUMNO",
        [["propio:ver_estado", "propio", "ver_estado"]],
    )
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="noperm@test.com", roles=["ALUMNO"],
    )

    result = await has_permission_with_scope(
        permiso_base="calificaciones:importar",
        user=user,
        resource_owner_id=user.id,
        db=db_session,
        use_cache=False,
    )

    assert result is False


# ===================================================================
# Scoping utility function tests
# ===================================================================


class TestScopingUtils:
    """Unit tests for _perm_is_global, _perm_base_code, _perm_propio_code."""

    @pytest.mark.parametrize(
        ("perm_code", "expected"),
        [
            ("calificaciones:importar", True),
            ("rbac:gestionar", True),
            ("calificaciones:importar:propio", False),
            ("auditoria:ver:propio", False),
        ],
    )
    def test_perm_is_global(self, perm_code: str, expected: bool) -> None:
        assert _perm_is_global(perm_code) is expected

    @pytest.mark.parametrize(
        ("perm_code", "expected_base"),
        [
            ("calificaciones:importar", "calificaciones:importar"),
            ("calificaciones:importar:propio", "calificaciones:importar"),
            ("auditoria:ver:propio", "auditoria:ver"),
        ],
    )
    def test_perm_base_code(self, perm_code: str, expected_base: str) -> None:
        assert _perm_base_code(perm_code) == expected_base

    @pytest.mark.parametrize(
        ("perm_code", "expected_propio"),
        [
            ("calificaciones:importar", "calificaciones:importar:propio"),
            ("calificaciones:importar:propio", "calificaciones:importar:propio"),
            ("auditoria:ver", "auditoria:ver:propio"),
        ],
    )
    def test_perm_propio_code(self, perm_code: str, expected_propio: str) -> None:
        assert _perm_propio_code(perm_code) == expected_propio
