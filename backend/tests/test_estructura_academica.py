from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import create_test_tenant, create_test_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_EMAIL = "admin@estructura.test"
_NO_PERM_EMAIL = "noperm@estructura.test"


async def _setup_admin(db_session: AsyncSession) -> dict:
    """Seed tenant + ADMIN role + estructura:gestionar permission + ADMIN user."""
    tenant = await create_test_tenant(db_session)

    role = Role(tenant_id=tenant.id, nombre="ADMIN", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="estructura:gestionar",
        modulo="estructura",
        accion="gestionar",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)
    await db_session.commit()

    user = await create_test_user(
        db_session, tenant_id=tenant.id, email=_ADMIN_EMAIL, roles=["ADMIN"],
    )

    return {
        "tenant": tenant,
        "user": user,
        "role": role,
        "perm": perm,
    }


async def _setup_second_tenant(db_session: AsyncSession) -> dict:
    """Seed a second tenant with ADMIN role and estructura:gestionar."""
    tenant = await create_test_tenant(
        db_session, slug="tenant-b", name="Tenant B"
    )

    role = Role(tenant_id=tenant.id, nombre="ADMIN", editable=False)
    perm = Permission(
        tenant_id=tenant.id,
        codigo="estructura:gestionar",
        modulo="estructura",
        accion="gestionar",
    )
    db_session.add_all([role, perm])
    await db_session.flush()
    await db_session.refresh(role)
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)
    await db_session.commit()

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="admin2@estructura.test",
        roles=["ADMIN"],
    )

    return {
        "tenant": tenant,
        "user": user,
    }


async def _login(client: TestClient, email: str = _ADMIN_EMAIL) -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


async def _auth_header(client: TestClient, email: str = _ADMIN_EMAIL) -> dict:
    token = await _login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# 8.1-8.8 — Carrera CRUD
# ===================================================================


@pytest.mark.asyncio
async def test_create_carrera_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/carreras → 201 with estado: Activa."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Tecnicatura Univ. en Programación"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "TUP"
    assert data["nombre"] == "Tecnicatura Univ. en Programación"
    assert data["estado"] == "Activa"
    assert UUID(data["id"])
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_carrera_duplicate_codigo_409(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/carreras with duplicate codigo → 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Original"},
        headers=headers,
    )
    response = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Duplicate"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "ya existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_carrera_same_codigo_different_tenant_201(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Same codigo in different tenants → both 201 (isolation)."""
    clear_all_caches()
    setup_a = await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@estructura.test")

    resp_a = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Tenant A"},
        headers=headers_a,
    )
    assert resp_a.status_code == 201

    resp_b = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Tenant B"},
        headers=headers_b,
    )
    assert resp_b.status_code == 201
    assert resp_b.json()["codigo"] == "TUP"


@pytest.mark.asyncio
async def test_list_carreras_tenant_scoped(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/carreras only returns tenant's carreras."""
    clear_all_caches()
    setup_a = await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@estructura.test")

    # Create one carrera in each tenant
    client.post(
        "/api/admin/carreras",
        json={"codigo": "CARR-A", "nombre": "Carrera A"},
        headers=headers_a,
    )
    client.post(
        "/api/admin/carreras",
        json={"codigo": "CARR-B", "nombre": "Carrera B"},
        headers=headers_b,
    )

    # Tenant A should only see CARR-A
    resp_a = client.get("/api/admin/carreras", headers=headers_a)
    assert resp_a.status_code == 200
    codigos_a = [c["codigo"] for c in resp_a.json()]
    assert "CARR-A" in codigos_a
    assert "CARR-B" not in codigos_a


@pytest.mark.asyncio
async def test_get_carrera_not_found_404(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/carreras/{nonexistent} → 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.get(f"/api/admin/carreras/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_carrera_200(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/carreras/{id} updates fields."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "Original"},
        headers=headers,
    )
    carrera_id = create_resp.json()["id"]

    response = client.put(
        f"/api/admin/carreras/{carrera_id}",
        json={"codigo": "TUPV2", "nombre": "Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "TUPV2"
    assert data["nombre"] == "Updated"


@pytest.mark.asyncio
async def test_update_carrera_duplicate_codigo_409(
    client: TestClient, db_session: AsyncSession
) -> None:
    """PUT /api/admin/carreras/{id} with duplicate codigo → 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "First"},
        headers=headers,
    )
    create2 = client.post(
        "/api/admin/carreras",
        json={"codigo": "OTRA", "nombre": "Second"},
        headers=headers,
    )
    otra_id = create2.json()["id"]

    response = client.put(
        f"/api/admin/carreras/{otra_id}",
        json={"codigo": "TUP"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "ya existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_carrera_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/carreras/{id} soft-deletes and removes from list."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post(
        "/api/admin/carreras",
        json={"codigo": "TUP", "nombre": "To Delete"},
        headers=headers,
    )
    carrera_id = create_resp.json()["id"]

    response = client.delete(f"/api/admin/carreras/{carrera_id}", headers=headers)
    assert response.status_code == 204

    list_resp = client.get("/api/admin/carreras", headers=headers)
    codigos = [c["codigo"] for c in list_resp.json()]
    assert "TUP" not in codigos


# ===================================================================
# 8.9-8.15 — Cohorte CRUD
# ===================================================================


async def _create_carrera(
    client: TestClient, headers: dict, codigo: str = "TUP"
) -> dict:
    resp = client.post(
        "/api/admin/carreras",
        json={"codigo": codigo, "nombre": f"Carrera {codigo}"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_create_cohorte_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/cohortes → 201."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)

    response = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "MAR-2026"
    assert data["anio"] == 2026
    assert data["vig_hasta"] is None
    assert data["estado"] == "Activa"
    assert UUID(data["id"])


@pytest.mark.asyncio
async def test_create_cohorte_duplicate_nombre_409(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/cohortes with duplicate name (same carrera) → 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)

    client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    response = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2027,
            "vig_desde": "2027-03-01",
        },
        headers=headers,
    )
    assert response.status_code == 409
    assert "ya existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_cohorte_same_nombre_different_carrera_201(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Same cohorte nombre in different carreras → both 201."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_a = await _create_carrera(client, headers, codigo="TUP")
    carrera_b = await _create_carrera(client, headers, codigo="TSP")

    resp_a = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_a["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    assert resp_a.status_code == 201

    resp_b = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_b["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_create_cohorte_carrera_inactiva_abierta_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/cohortes with vig_hasta=null on inactive carrera → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)

    # Set carrera to inactive
    client.put(
        f"/api/admin/carreras/{carrera['id']}",
        json={"estado": "Inactiva"},
        headers=headers,
    )

    response = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert "no se pueden crear cohortes abiertas" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_cohorte_carrera_inactiva_cerrada_201(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/cohortes with vig_hasta set on inactive carrera → 201."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)

    client.put(
        f"/api/admin/carreras/{carrera['id']}",
        json={"estado": "Inactiva"},
        headers=headers,
    )

    response = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers=headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_cohorte_abrir_en_carrera_inactiva_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """PUT /api/admin/cohortes setting vig_hasta=null when carrera inactive → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)

    # Create cohorte with vig_hasta set (closed)
    create_resp = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers=headers,
    )
    cohorte_id = create_resp.json()["id"]

    # Set carrera to inactive
    client.put(
        f"/api/admin/carreras/{carrera['id']}",
        json={"estado": "Inactiva"},
        headers=headers,
    )

    # Try to open the cohorte (set vig_hasta to null)
    response = client.put(
        f"/api/admin/cohortes/{cohorte_id}",
        json={"vig_hasta": None},
        headers=headers,
    )
    assert response.status_code == 422
    assert "no se pueden crear cohortes abiertas" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_cohorte_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/cohortes/{id} soft-deletes."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera = await _create_carrera(client, headers)
    create_resp = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera["id"],
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    cohorte_id = create_resp.json()["id"]

    response = client.delete(f"/api/admin/cohortes/{cohorte_id}", headers=headers)
    assert response.status_code == 204

    list_resp = client.get("/api/admin/cohortes", headers=headers)
    nombres = [c["nombre"] for c in list_resp.json()]
    assert "MAR-2026" not in nombres


# ===================================================================
# 8.16-8.20 — Materia CRUD
# ===================================================================


@pytest.mark.asyncio
async def test_create_materia_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/materias → 201 with estado: Activa."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    response = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Programación I"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "PROG_I"
    assert data["nombre"] == "Programación I"
    assert data["estado"] == "Activa"
    assert UUID(data["id"])


@pytest.mark.asyncio
async def test_create_materia_duplicate_codigo_409(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/materias with duplicate codigo → 409."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Original"},
        headers=headers,
    )
    response = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Duplicate"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "ya existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_materia_same_codigo_different_tenant_201(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Same codigo in different tenants → both 201 (isolation)."""
    clear_all_caches()
    await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@estructura.test")

    resp_a = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Tenant A"},
        headers=headers_a,
    )
    assert resp_a.status_code == 201

    resp_b = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Tenant B"},
        headers=headers_b,
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_list_materias_tenant_scoped(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/materias only returns tenant's materias."""
    clear_all_caches()
    await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@estructura.test")

    client.post(
        "/api/admin/materias",
        json={"codigo": "MAT-A", "nombre": "Materia A"},
        headers=headers_a,
    )
    client.post(
        "/api/admin/materias",
        json={"codigo": "MAT-B", "nombre": "Materia B"},
        headers=headers_b,
    )

    resp_a = client.get("/api/admin/materias", headers=headers_a)
    assert resp_a.status_code == 200
    codigos = [m["codigo"] for m in resp_a.json()]
    assert "MAT-A" in codigos
    assert "MAT-B" not in codigos


@pytest.mark.asyncio
async def test_delete_materia_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/materias/{id} soft-deletes."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    create_resp = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "To Delete"},
        headers=headers,
    )
    materia_id = create_resp.json()["id"]

    response = client.delete(f"/api/admin/materias/{materia_id}", headers=headers)
    assert response.status_code == 204

    list_resp = client.get("/api/admin/materias", headers=headers)
    codigos = [m["codigo"] for m in list_resp.json()]
    assert "PROG_I" not in codigos


# ===================================================================
# 8.21 — Sin autenticación → 401
# 8.22 — Sin permiso → 403
# ===================================================================


@pytest.mark.asyncio
async def test_carreras_unauthenticated_401(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/carreras without token → 401."""
    await _setup_admin(db_session)
    response = client.get("/api/admin/carreras")
    assert response.status_code == 401

    response = client.post("/api/admin/carreras", json={"codigo": "X", "nombre": "X"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cohortes_unauthenticated_401(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/cohortes without token → 401."""
    await _setup_admin(db_session)
    response = client.get("/api/admin/cohortes")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_materias_unauthenticated_401(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/materias without token → 401."""
    await _setup_admin(db_session)
    response = client.get("/api/admin/materias")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_carreras_forbidden_403(
    client: TestClient, db_session: AsyncSession
) -> None:
    """User without estructura:gestionar → 403 on carreras endpoint."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)

    role = Role(tenant_id=tenant.id, nombre="PROFESOR")
    db_session.add(role)
    await db_session.commit()

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_NO_PERM_EMAIL,
        roles=["PROFESOR"],
    )

    headers = await _auth_header(client, email=_NO_PERM_EMAIL)
    response = client.get("/api/admin/carreras", headers=headers)
    assert response.status_code == 403

    response = client.post(
        "/api/admin/carreras",
        json={"codigo": "X", "nombre": "X"},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cohortes_forbidden_403(
    client: TestClient, db_session: AsyncSession
) -> None:
    """User without estructura:gestionar → 403 on cohortes endpoint."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)

    role = Role(tenant_id=tenant.id, nombre="PROFESOR")
    db_session.add(role)
    await db_session.commit()

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_NO_PERM_EMAIL,
        roles=["PROFESOR"],
    )

    headers = await _auth_header(client, email=_NO_PERM_EMAIL)
    response = client.get("/api/admin/cohortes", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_materias_forbidden_403(
    client: TestClient, db_session: AsyncSession
) -> None:
    """User without estructura:gestionar → 403 on materias endpoint."""
    clear_all_caches()
    tenant = await create_test_tenant(db_session)

    role = Role(tenant_id=tenant.id, nombre="PROFESOR")
    db_session.add(role)
    await db_session.commit()

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_NO_PERM_EMAIL,
        roles=["PROFESOR"],
    )

    headers = await _auth_header(client, email=_NO_PERM_EMAIL)
    response = client.get("/api/admin/materias", headers=headers)
    assert response.status_code == 403
