"""Integration tests for ``GET /api/admin/audit-log``.

These tests exercise the full stack (router → permissions → repository
→ database) using FastAPI's ``TestClient`` connected to a real
PostgreSQL database.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.services.audit_service import AuditService
from tests.conftest import create_test_tenant, create_test_user

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ADMIN_EMAIL = "admin@audit.test"
_PROFESOR_EMAIL = "profesor@audit.test"
_PROPIO_EMAIL = "propio@audit.test"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_admin(db_session: AsyncSession) -> dict:
    """Seed tenant with ADMIN role + auditoria:ver permission + user."""
    tenant = await create_test_tenant(db_session, slug="audit-tenant", name="Audit Tenant")

    role = Role(tenant_id=tenant.id, nombre="ADMIN", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="auditoria:ver",
        modulo="auditoria",
        accion="ver",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)
    await db_session.flush()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_ADMIN_EMAIL, roles=["ADMIN"],
    )

    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "perm": perm,
    }


async def _setup_propio_user(db_session: AsyncSession) -> dict:
    """Seed tenant + user with only auditoria:ver:propio permission."""
    tenant = await create_test_tenant(db_session, slug="propio-tenant", name="Propio Tenant")

    role = Role(tenant_id=tenant.id, nombre="COORDINADOR", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="auditoria:ver:propio",
        modulo="auditoria",
        accion="ver",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)
    await db_session.flush()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_PROPIO_EMAIL, roles=["COORDINADOR"],
    )

    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "perm": perm,
    }


async def _setup_no_permission_user(db_session: AsyncSession) -> dict:
    """Seed tenant + user WITHOUT any auditoria:ver permission."""
    tenant = await create_test_tenant(db_session, slug="no-perm-tenant", name="No Perm Tenant")

    role = Role(tenant_id=tenant.id, nombre="PROFESOR", editable=False)
    db_session.add(role)
    await db_session.flush()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_PROFESOR_EMAIL, roles=["PROFESOR"],
    )

    return {"tenant": tenant, "user": user, "role": role}


async def _login(client: TestClient, email: str = _ADMIN_EMAIL) -> str:
    """Login and return access token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


async def _auth_header(client: TestClient, email: str = _ADMIN_EMAIL) -> dict:
    """Return Authorization header dict for a logged-in user."""
    token = await _login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


async def _seed_audit_entries(
    db_session: AsyncSession, tenant_id, actor_id, count: int = 3
) -> None:
    """Create ``count`` audit log entries for the given actor."""
    service = AuditService(db=db_session, tenant_id=tenant_id, ip="10.0.0.1")
    for i in range(count):
        await service.register(
            actor_id=actor_id,
            accion="CALIFICACIONES_IMPORTAR",
            detalle={"seq": i},
            filas_afectadas=i * 10,
        )
    await db_session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAuditLogAPI:
    """GET /api/admin/audit-log endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_without_filters(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """User with auditoria:ver → 200 + paginated list."""
        clear_all_caches()
        setup = await _setup_admin(db_session)
        await _seed_audit_entries(
            db_session, setup["tenant"].id, setup["user"].id, count=3
        )

        headers = await _auth_header(client)
        response = client.get("/api/admin/audit-log", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 3
        assert len(data["entries"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 50

    @pytest.mark.asyncio
    async def test_list_empty_log(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """No entries → 200 with empty list."""
        clear_all_caches()
        await _setup_admin(db_session)

        headers = await _auth_header(client)
        response = client.get("/api/admin/audit-log", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["entries"] == []

    @pytest.mark.asyncio
    async def test_filter_by_accion(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Filter by accion returns only matching entries."""
        clear_all_caches()
        setup = await _setup_admin(db_session)
        service = AuditService(
            db=db_session, tenant_id=setup["tenant"].id, ip="10.0.0.1"
        )
        await service.register(
            actor_id=setup["user"].id, accion="CALIFICACIONES_IMPORTAR"
        )
        await service.register(
            actor_id=setup["user"].id, accion="PADRON_CARGAR"
        )
        await db_session.commit()

        headers = await _auth_header(client)
        response = client.get(
            "/api/admin/audit-log?accion=CALIFICACIONES_IMPORTAR",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["accion"] == "CALIFICACIONES_IMPORTAR"

    @pytest.mark.asyncio
    async def test_filter_by_actor_id(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Filter by actor_id returns only entries by that user."""
        clear_all_caches()
        setup = await _setup_admin(db_session)
        tenant = setup["tenant"]
        user = setup["user"]

        # Create a second user and seed entries for both
        other_user = await create_test_user(
            db_session,
            tenant_id=tenant.id,
            email="other@audit.test",
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(actor_id=user.id, accion="CALIFICACIONES_IMPORTAR")
        await service.register(actor_id=other_user.id, accion="PADRON_CARGAR")
        await db_session.commit()

        headers = await _auth_header(client)
        response = client.get(
            f"/api/admin/audit-log?actor_id={user.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["actor_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_pagination(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Pagination params limit results."""
        clear_all_caches()
        setup = await _setup_admin(db_session)
        await _seed_audit_entries(
            db_session, setup["tenant"].id, setup["user"].id, count=5
        )

        headers = await _auth_header(client)
        response = client.get(
            "/api/admin/audit-log?page=1&page_size=2",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["entries"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_no_permission_returns_403(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """User without auditoria:ver → 403."""
        clear_all_caches()
        setup = await _setup_no_permission_user(db_session)

        # Verify user has no auditoria permission
        headers = await _auth_header(client, email=_PROFESOR_EMAIL)
        response = client.get("/api/admin/audit-log", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """No token → 401."""
        clear_all_caches()
        await _setup_admin(db_session)
        response = client.get("/api/admin/audit-log")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_propio_user_sees_only_own_actions(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """User with only auditoria:ver:propio → only sees own entries."""
        clear_all_caches()
        setup = await _setup_propio_user(db_session)
        tenant = setup["tenant"]
        user = setup["user"]

        # Create a second user in the same tenant
        other_user = await create_test_user(
            db_session,
            tenant_id=tenant.id,
            email="other2@audit.test",
        )

        # Seed entries: 1 for the propio user, 2 for other user
        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(actor_id=user.id, accion="CALIFICACIONES_IMPORTAR")
        await service.register(actor_id=other_user.id, accion="PADRON_CARGAR")
        await service.register(actor_id=other_user.id, accion="PADRON_CARGAR")
        await db_session.commit()

        headers = await _auth_header(client, email=_PROPIO_EMAIL)
        response = client.get("/api/admin/audit-log", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Should only see their own entry
        assert data["total"] == 1
        assert data["entries"][0]["actor_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_propio_user_with_explicit_actor_id_still_scoped(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Propio user can't bypass scope by passing actor_id param."""
        clear_all_caches()
        setup = await _setup_propio_user(db_session)
        tenant = setup["tenant"]
        user = setup["user"]

        other_user = await create_test_user(
            db_session,
            tenant_id=tenant.id,
            email="other3@audit.test",
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(actor_id=other_user.id, accion="PADRON_CARGAR")
        await db_session.commit()

        headers = await _auth_header(client, email=_PROPIO_EMAIL)
        # Try to see other user's entries via explicit filter
        response = client.get(
            f"/api/admin/audit-log?actor_id={other_user.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Should be scoped to self, showing 0 entries (other_user's filtered out)
        assert data["total"] == 0
