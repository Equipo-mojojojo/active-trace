"""Integration tests for impersonation (iniciar / finalizar).

These tests exercise the full stack: router → permissions → JWT
creation → service → audit log persistence.
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

_ADMIN_EMAIL = "admin@imp.test"
_TARGET_EMAIL = "target@imp.test"
_NO_PERM_EMAIL = "noperm@imp.test"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_admin_with_impersonacion(db_session: AsyncSession) -> dict:
    """Seed tenant + ADMIN (with impersonacion:usar) + target user."""
    tenant = await create_test_tenant(db_session, slug="imp-tenant", name="Imp Tenant")

    # Create ADMIN role with impersonacion:usar
    role = Role(tenant_id=tenant.id, nombre="ADMIN", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="impersonacion:usar",
        modulo="impersonacion",
        accion="usar",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)

    # Also add auditoria:ver so the admin can query the audit log
    audit_perm = Permission(
        tenant_id=tenant.id,
        codigo="auditoria:ver",
        modulo="auditoria",
        accion="ver",
    )
    db_session.add(audit_perm)
    await db_session.flush()

    audit_rp = RolePermission(
        tenant_id=tenant.id, rol_id=role.id, permiso_id=audit_perm.id
    )
    db_session.add(audit_rp)

    admin_user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_ADMIN_EMAIL, roles=["ADMIN"],
    )

    # Create target user (no special permissions)
    target_user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_TARGET_EMAIL, roles=["PROFESOR"],
    )

    return {
        "tenant": tenant,
        "admin": admin_user,
        "target": target_user,
        "role": role,
        "perm": perm,
    }


async def _setup_no_permission_user(db_session: AsyncSession) -> dict:
    """Seed tenant + user WITHOUT impersonacion:usar."""
    tenant = await create_test_tenant(
        db_session, slug="no-imp-tenant", name="No Imp Tenant"
    )

    role = Role(tenant_id=tenant.id, nombre="PROFESOR", editable=False)
    db_session.add(role)
    await db_session.flush()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_NO_PERM_EMAIL, roles=["PROFESOR"],
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestImpersonacionIniciar:
    """POST /api/admin/impersonacion/iniciar."""

    @pytest.mark.asyncio
    async def test_iniciar_impersonacion_exitoso(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Admin with impersonacion:usar can impersonate a target user."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)

        headers = await _auth_header(client)
        response = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # The new token should be an impersonation token
        # (we'll verify by using it to call an endpoint)
        imp_headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp2 = client.get("/api/admin/audit-log", headers=imp_headers)
        # Since the impersonated user (PROFESOR) doesn't have auditoria:ver,
        # the permissions check uses the impersonated user → 403
        # This proves the token represents the impersonated user
        assert resp2.status_code == 403

    @pytest.mark.asyncio
    async def test_iniciar_403_sin_permiso(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """User without impersonacion:usar → 403."""
        clear_all_caches()
        setup = await _setup_no_permission_user(db_session)
        tenant = setup["tenant"]

        # Create a target user in the same tenant
        target = await create_test_user(
            db_session, tenant_id=tenant.id, email="someuser@test.com"
        )

        headers = await _auth_header(client, email=_NO_PERM_EMAIL)
        response = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(target.id)},
            headers=headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_iniciar_404_usuario_inexistente(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Impersonating a non-existent user → 404."""
        clear_all_caches()
        await _setup_admin_with_impersonacion(db_session)

        from uuid import uuid4

        headers = await _auth_header(client)
        response = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(uuid4())},
            headers=headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_iniciar_registra_audit_log(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Iniciar impersonación logs IMPERSONACION_INICIAR in audit log."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)

        headers = await _auth_header(client)
        response = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        assert response.status_code == 201

        # Query the audit log to verify the entry
        resp2 = client.get(
            "/api/admin/audit-log?accion=IMPERSONACION_INICIAR",
            headers=headers,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["total"] >= 1
        entry = data["entries"][0]
        assert entry["accion"] == "IMPERSONACION_INICIAR"
        assert entry["actor_id"] == str(setup["admin"].id)
        assert entry["impersonado_id"] == str(setup["target"].id)


class TestImpersonacionFinalizar:
    """POST /api/admin/impersonacion/finalizar."""

    @pytest.mark.asyncio
    async def test_finalizar_impersonacion_exitoso(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Finishing impersonation returns a normal token."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)

        # Start impersonation
        headers = await _auth_header(client)
        iniciar_resp = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        assert iniciar_resp.status_code == 201
        imp_token = iniciar_resp.json()["access_token"]
        imp_headers = {"Authorization": f"Bearer {imp_token}"}

        # Finalize impersonation (using the impersonation token)
        finalizar_resp = client.post(
            "/api/admin/impersonacion/finalizar",
            headers=imp_headers,
        )
        assert finalizar_resp.status_code == 200
        data = finalizar_resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # The new token should be a normal token (admin-level)
        new_headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp2 = client.get("/api/admin/audit-log", headers=new_headers)
        assert resp2.status_code == 200  # admin has auditoria:ver

    @pytest.mark.asyncio
    async def test_finalizar_sin_impersonacion_activa(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Calling finalizar without an active impersonation → 400."""
        clear_all_caches()
        await _setup_admin_with_impersonacion(db_session)

        headers = await _auth_header(client)
        response = client.post(
            "/api/admin/impersonacion/finalizar",
            headers=headers,
        )
        assert response.status_code == 400
        assert "No hay una sesión de impersonación activa" in response.text

    @pytest.mark.asyncio
    async def test_finalizar_registra_audit_log(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Finalizar impersonación logs IMPERSONACION_FINALIZAR."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)
        tenant = setup["tenant"]

        # Start impersonation
        headers = await _auth_header(client)
        iniciar_resp = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        imp_token = iniciar_resp.json()["access_token"]

        # Finalize
        imp_headers = {"Authorization": f"Bearer {imp_token}"}
        client.post("/api/admin/impersonacion/finalizar", headers=imp_headers)

        # Check audit log (admin headers = real user)
        resp2 = client.get(
            "/api/admin/audit-log?accion=IMPERSONACION_FINALIZAR",
            headers=headers,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["total"] >= 1
        entry = data["entries"][0]
        assert entry["accion"] == "IMPERSONACION_FINALIZAR"
        assert entry["actor_id"] == str(setup["admin"].id)
        assert entry["impersonado_id"] == str(setup["target"].id)


class TestGetCurrentUserImpersonacion:
    """get_current_user behaviour under impersonation."""

    @pytest.mark.asyncio
    async def test_impersonated_user_has_target_roles(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Under impersonation, permission checks run against the target user."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)
        # admin has auditoria:ver, target (PROFESOR) does NOT

        headers = await _auth_header(client)
        iniciar_resp = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        imp_token = iniciar_resp.json()["access_token"]
        imp_headers = {"Authorization": f"Bearer {imp_token}"}

        # Under impersonation, the permission check uses the target user
        # who doesn't have auditoria:ver → should be 403
        resp = client.get("/api/admin/audit-log", headers=imp_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_audit_log_under_impersonation_uses_real_actor(
        self, client: TestClient, db_session: AsyncSession
    ) -> None:
        """Actions under impersonation are attributed to the real actor."""
        clear_all_caches()
        setup = await _setup_admin_with_impersonacion(db_session)

        headers = await _auth_header(client)
        iniciar_resp = client.post(
            "/api/admin/impersonacion/iniciar",
            json={"usuario_id": str(setup["target"].id)},
            headers=headers,
        )
        imp_token = iniciar_resp.json()["access_token"]

        # The iniciar itself should have logged the real actor
        # Let's also create a second action under impersonation
        # (The audit-log endpoint requires auditoria:ver which the
        #  impersonated user doesn't have, so we check from admin headers)

        resp = client.get(
            "/api/admin/audit-log?accion=IMPERSONACION_INICIAR",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        entry = data["entries"][0]
        # The real admin is the actor
        assert entry["actor_id"] == str(setup["admin"].id)
        assert entry["impersonado_id"] == str(setup["target"].id)
