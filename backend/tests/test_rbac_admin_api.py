from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    clear_all_caches,
    get_cached_permissions,
    get_effective_permissions,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import create_test_tenant, create_test_user

# ---------------------------------------------------------------------------
# Helpers de setup para tests de API
# ---------------------------------------------------------------------------

_ADMIN_EMAIL = "admin@rbac.test"
_PROFESOR_EMAIL = "profesor@rbac.test"


async def _setup_admin(db_session: AsyncSession) -> dict:
    """Seed tenant + ADMIN role + rbac:gestionar permission + ADMIN user."""
    tenant = await create_test_tenant(db_session)

    role = Role(tenant_id=tenant.id, nombre="ADMIN", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="rbac:gestionar",
        modulo="rbac",
        accion="gestionar",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)

    extra_perm = Permission(
        tenant_id=tenant.id,
        codigo="calificaciones:importar",
        modulo="calificaciones",
        accion="importar",
    )
    db_session.add(extra_perm)
    await db_session.flush()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_ADMIN_EMAIL, roles=["ADMIN"],
    )
    # user ya tiene commit por create_test_user

    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "perm": perm,
        "extra_perm": extra_perm,
    }


async def _login(client: TestClient, email: str = _ADMIN_EMAIL) -> str:
    """Login and return access token."""
    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


async def _auth_header(client: TestClient, email: str = _ADMIN_EMAIL) -> dict:
    """Return Authorization header dict for a logged-in user."""
    token = await _login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# 4.3 — Guard tests (require_permission)
# ===================================================================


@pytest.mark.asyncio
async def test_admin_can_list_roles(client: TestClient, db_session: AsyncSession) -> None:
    """User with rbac:gestionar → 200 on admin endpoint."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)
    # Also verify the identity comes from the token, not query params
    response = client.get("/api/admin/roles?user_id=spoofed&tenant_id=spoofed", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_non_admin_gets_403(client: TestClient, db_session: AsyncSession) -> None:
    """User without rbac:gestionar → 403 on admin endpoint."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)

    # Create PROFESOR (which doesn't have rbac:gestionar)
    role = Role(tenant_id=tenant.id, nombre="PROFESOR")
    db_session.add(role)
    await db_session.commit()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_PROFESOR_EMAIL, roles=["PROFESOR"],
    )

    headers = await _auth_header(client, email=_PROFESOR_EMAIL)
    response = client.get("/api/admin/roles", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_gets_401(client: TestClient, db_session: AsyncSession) -> None:
    """No token → 401 on admin endpoint."""
    await _setup_admin(db_session)
    response = client.get("/api/admin/roles")
    assert response.status_code == 401


# ===================================================================
# 4.4 — Fail-closed test
# ===================================================================


@pytest.mark.asyncio
async def test_require_permission_fail_closed_returns_403(db_session: AsyncSession) -> None:
    """If get_effective_permissions raises, require_permission returns 403, not 500."""
    from unittest.mock import patch

    from fastapi import HTTPException

    from app.core.permissions import require_permission

    clear_all_caches()
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(
        db_session, tenant_id=tenant.id, email="fail@test.com", roles=["ADMIN"],
    )

    guard = require_permission("rbac:gestionar")

    # Mock get_effective_permissions to simulate a DB failure
    with patch(
        "app.core.permissions.get_effective_permissions",
        side_effect=Exception("Simulated DB error"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await guard(user=user, db=db_session)

    assert exc_info.value.status_code == 403
    assert "access denied" in exc_info.value.detail


# ===================================================================
# 6.11 — Admin API integration tests
# ===================================================================


@pytest.mark.asyncio
async def test_list_roles_empty(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/roles returns empty list when no roles exist besides seed."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.get("/api/admin/roles", headers=headers)
    assert response.status_code == 200
    # The test DB was created from scratch with seed in migration,
    # but db_session fixture does drop_all/create_all which skips alembic seed.
    # So we expect only the role created in _setup_admin
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "ADMIN"


@pytest.mark.asyncio
async def test_create_role_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/roles creates a new role."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "Ayudante de cátedra"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "TUTOR"
    assert data["descripcion"] == "Ayudante de cátedra"
    assert data["editable"] is True
    assert UUID(data["id"])


@pytest.mark.asyncio
async def test_create_role_extra_fields_rejected(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/roles with extra fields returns 422 (extra='forbid')."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "Tutor", "extra_field": "forbidden"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_role_duplicate_returns_409(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/roles with duplicate name returns 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    resp1 = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "First"},
        headers=headers,
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "Duplicate"},
        headers=headers,
    )
    assert resp2.status_code == 409
    assert "Ya existe" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_update_role_200(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/roles/{id} updates name and description."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    # Create a role to update
    create_resp = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "Original"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]

    response = client.put(
        f"/api/admin/roles/{role_id}",
        json={"nombre": "TUTOR_V2", "descripcion": "Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "TUTOR_V2"
    assert data["descripcion"] == "Updated"


@pytest.mark.asyncio
async def test_update_role_nonexistent_returns_404(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/roles/{nonexistent} returns 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.put(
        f"/api/admin/roles/{fake_id}",
        json={"nombre": "FAKE"},
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Rol no encontrado"


@pytest.mark.asyncio
async def test_update_role_duplicate_name_returns_409(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/roles/{id} with name that already exists returns 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    create2 = client.post("/api/admin/roles", json={"nombre": "OTRO"}, headers=headers)
    otro_id = create2.json()["id"]

    # Try updating "OTRO" to "TUTOR" (which already exists)
    response = client.put(
        f"/api/admin/roles/{otro_id}",
        json={"nombre": "TUTOR"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "Ya existe" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_role_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/roles/{id} soft-deletes the role."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR", "descripcion": "To delete"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]

    response = client.delete(f"/api/admin/roles/{role_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone from list
    list_resp = client.get("/api/admin/roles", headers=headers)
    nombres = [r["nombre"] for r in list_resp.json()]
    assert "TUTOR" not in nombres


@pytest.mark.asyncio
async def test_delete_role_nonexistent_returns_404(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/roles/{nonexistent} returns 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.delete(f"/api/admin/roles/{fake_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_permissions_200(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/permisos returns all permissions."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.get("/api/admin/permisos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # _setup_admin creates: rbac:gestionar, calificaciones:importar
    codes = [p["codigo"] for p in data]
    assert "rbac:gestionar" in codes
    assert "calificaciones:importar" in codes


@pytest.mark.asyncio
async def test_list_permissions_filter_by_modulo(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/permisos?modulo=rbac filters by module."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.get("/api/admin/permisos?modulo=rbac", headers=headers)
    assert response.status_code == 200
    data = response.json()
    codes = [p["codigo"] for p in data]
    assert "rbac:gestionar" in codes
    assert "calificaciones:importar" not in codes


@pytest.mark.asyncio
async def test_assign_permission_to_role_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/roles/{id}/permisos assigns permission."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post(
        "/api/admin/roles",
        json={"nombre": "TUTOR"},
        headers=headers,
    )
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    response = client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_assign_permission_nonexistent_role_returns_404(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """POST /api/admin/roles/{nonexistent}/permisos returns 404."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)
    perm_id = str(setup["extra_perm"].id)

    fake_role_id = "00000000-0000-0000-0000-000000000001"
    response = client.post(
        f"/api/admin/roles/{fake_role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_nonexistent_permission_returns_404(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """POST /api/admin/roles/{id}/permisos with bad perm_id returns 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    fake_perm_id = "00000000-0000-0000-0000-000000000999"

    response = client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": fake_perm_id},
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Permiso no encontrado"


@pytest.mark.asyncio
async def test_remove_permission_from_role_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/roles/{id}/permisos/{perm_id} removes the assignment."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    # First assign
    client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )

    # Then remove
    response = client.delete(
        f"/api/admin/roles/{role_id}/permisos/{perm_id}",
        headers=headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_permission_not_assigned_returns_404(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """DELETE /api/admin/roles/{id}/permisos/{perm_id} without assignment returns 404."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    response = client.delete(
        f"/api/admin/roles/{role_id}/permisos/{perm_id}",
        headers=headers,
    )
    assert response.status_code == 404
    assert "no tiene ese permiso" in response.json()["detail"]


@pytest.mark.asyncio
async def test_assign_duplicate_permission_raises_integrity_error(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """Assigning the same permission twice triggers IntegrityError.

    ⚠️ Known gap: the service does not check for existing assignments before
    inserting. The DB unique constraint fires, but the IntegrityError propagates
    through get_db() → Starlette testclient as an exception rather than a 500.
    Ideally this should return 409 Conflict.
    """
    import sqlalchemy.exc

    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    # First assignment succeeds
    resp1 = client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )
    assert resp1.status_code == 201

    # Second assignment — IntegrityError burbles up through testclient
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        client.post(
            f"/api/admin/roles/{role_id}/permisos",
            json={"permiso_id": perm_id},
            headers=headers,
        )


# ===================================================================
# 6.12 — Cache invalidation via API
# ===================================================================


@pytest.mark.asyncio
async def test_cache_invalidated_when_permission_assigned(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """Assigning a permission to a role invalidates the tenant's cache."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    # First call populates the cache
    resp1 = client.get("/api/admin/roles", headers=headers)
    assert resp1.status_code == 200

    # Verify cache is populated
    cached = get_cached_permissions(setup["tenant"].id, setup["user"].id)
    assert cached is not None

    # Create a new role and assign a permission — this should invalidate
    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )

    # Cache should be invalidated
    assert get_cached_permissions(setup["tenant"].id, setup["user"].id) is None


@pytest.mark.asyncio
async def test_cache_invalidated_when_permission_removed(
    client: TestClient, db_session: AsyncSession,
) -> None:
    """Removing a permission from a role invalidates the tenant's cache."""
    clear_all_caches()
    setup = await _setup_admin(db_session)
    headers = await _auth_header(client)

    # Create role and assign permission
    create_resp = client.post("/api/admin/roles", json={"nombre": "TUTOR"}, headers=headers)
    role_id = create_resp.json()["id"]
    perm_id = str(setup["extra_perm"].id)

    client.post(
        f"/api/admin/roles/{role_id}/permisos",
        json={"permiso_id": perm_id},
        headers=headers,
    )

    # Populate the cache
    resp = client.get("/api/admin/roles", headers=headers)
    assert resp.status_code == 200
    assert get_cached_permissions(setup["tenant"].id, setup["user"].id) is not None

    # Remove permission — cache should be invalidated
    client.delete(
        f"/api/admin/roles/{role_id}/permisos/{perm_id}",
        headers=headers,
    )

    assert get_cached_permissions(setup["tenant"].id, setup["user"].id) is None
