from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import create_test_tenant, create_test_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_EMAIL = "admin@c17.test"


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
        db_session, slug="tenant-b-c17", name="Tenant B C17"
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
        email="admin2@c17.test",
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
# ProgramaMateria CRUD
# ===================================================================


@pytest.mark.asyncio
async def test_create_programa_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/programas → 201 with cargado_at."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    # First create a carrera, cohorte, materia
    carrera_resp = client.post(
        "/api/admin/carreras",
        json={"codigo": "C17C", "nombre": "Carrera C17"},
        headers=headers,
    )
    assert carrera_resp.status_code == 201
    carrera_id = carrera_resp.json()["id"]

    cohorte_resp = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers=headers,
    )
    assert cohorte_resp.status_code == 201
    cohorte_id = cohorte_resp.json()["id"]

    materia_resp = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_C17", "nombre": "Programación C17"},
        headers=headers,
    )
    assert materia_resp.status_code == 201
    materia_id = materia_resp.json()["id"]

    response = client.post(
        "/api/admin/programas",
        json={
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
            "titulo": "Programa Oficial 2026",
            "referencia_archivo": "s3://bucket/prog-c17-v1.pdf",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Programa Oficial 2026"
    assert data["referencia_archivo"] == "s3://bucket/prog-c17-v1.pdf"
    assert UUID(data["id"])
    assert UUID(data["materia_id"])
    assert UUID(data["carrera_id"])
    assert UUID(data["cohorte_id"])
    assert "cargado_at" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_programa_sin_referencia_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/programas without referencia_archivo → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras",
        json={"codigo": "C17C2", "nombre": "Carrera C17-2"},
        headers=headers,
    )
    carrera_id = carrera_resp.json()["id"]
    cohorte_resp = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "SEP-2026",
            "anio": 2026,
            "vig_desde": "2026-09-01",
        },
        headers=headers,
    )
    cohorte_id = cohorte_resp.json()["id"]
    materia_resp = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_C17B", "nombre": "Programación C17 B"},
        headers=headers,
    )
    materia_id = materia_resp.json()["id"]

    response = client.post(
        "/api/admin/programas",
        json={
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
            "titulo": "Sin archivo",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_programa_campos_extra_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/programas with extra campos → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras",
        json={"codigo": "C17C3", "nombre": "Carrera C17-3"},
        headers=headers,
    )
    carrera_id = carrera_resp.json()["id"]
    cohorte_resp = client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "OCT-2026",
            "anio": 2026,
            "vig_desde": "2026-10-01",
        },
        headers=headers,
    )
    cohorte_id = cohorte_resp.json()["id"]
    materia_resp = client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_C17C", "nombre": "Programación C17 C"},
        headers=headers,
    )
    materia_id = materia_resp.json()["id"]

    response = client.post(
        "/api/admin/programas",
        json={
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
            "titulo": "Extra",
            "referencia_archivo": "s3://bucket/x.pdf",
            "campo_extra": "no deberia estar",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_programas_con_filtros(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/programas with filters returns matching records."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    # Create two carreras, materias, cohortes
    c1_resp = client.post(
        "/api/admin/carreras", json={"codigo": "CARR1", "nombre": "Carrera 1"}, headers=headers
    )
    c1_id = c1_resp.json()["id"]
    c2_resp = client.post(
        "/api/admin/carreras", json={"codigo": "CARR2", "nombre": "Carrera 2"}, headers=headers
    )
    c2_id = c2_resp.json()["id"]

    coh1_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": c1_id, "nombre": "COH1", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    coh1_id = coh1_resp.json()["id"]
    coh2_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": c2_id, "nombre": "COH2", "anio": 2026, "vig_desde": "2026-06-01"},
        headers=headers,
    )
    coh2_id = coh2_resp.json()["id"]

    m1_resp = client.post(
        "/api/admin/materias", json={"codigo": "MAT1", "nombre": "Materia 1"}, headers=headers
    )
    m1_id = m1_resp.json()["id"]
    m2_resp = client.post(
        "/api/admin/materias", json={"codigo": "MAT2", "nombre": "Materia 2"}, headers=headers
    )
    m2_id = m2_resp.json()["id"]

    client.post(
        "/api/admin/programas",
        json={
            "materia_id": m1_id, "carrera_id": c1_id, "cohorte_id": coh1_id,
            "titulo": "Prog M1-C1", "referencia_archivo": "s3://b/m1c1.pdf",
        },
        headers=headers,
    )
    client.post(
        "/api/admin/programas",
        json={
            "materia_id": m2_id, "carrera_id": c2_id, "cohorte_id": coh2_id,
            "titulo": "Prog M2-C2", "referencia_archivo": "s3://b/m2c2.pdf",
        },
        headers=headers,
    )

    # Filter by materia_id
    resp = client.get(f"/api/admin/programas?materia_id={m1_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["titulo"] == "Prog M1-C1"

    # Filter by carrera_id
    resp = client.get(f"/api/admin/programas?carrera_id={c2_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["titulo"] == "Prog M2-C2"

    # Filter by cohorte_id
    resp = client.get(f"/api/admin/programas?cohorte_id={coh1_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["titulo"] == "Prog M1-C1"

    # No filter → all
    resp = client.get("/api/admin/programas", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_programa_200(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/programas/{id} → 200."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "GC1", "nombre": "Get Carrera"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "GETCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "GETMAT", "nombre": "Get Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/programas",
        json={
            "materia_id": mid, "carrera_id": cid, "cohorte_id": cohid,
            "titulo": "Get Prog", "referencia_archivo": "s3://b/get.pdf",
        },
        headers=headers,
    )
    prog_id = create_resp.json()["id"]

    response = client.get(f"/api/admin/programas/{prog_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["titulo"] == "Get Prog"


@pytest.mark.asyncio
async def test_get_programa_404(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/programas/{nonexistent} → 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.get(f"/api/admin/programas/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert "no encontrad" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_programa_200(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/programas/{id} updates fields."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "UC1", "nombre": "Upd Carrera"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "UPCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "UPMAT", "nombre": "Upd Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/programas",
        json={
            "materia_id": mid, "carrera_id": cid, "cohorte_id": cohid,
            "titulo": "Original", "referencia_archivo": "s3://b/orig.pdf",
        },
        headers=headers,
    )
    prog_id = create_resp.json()["id"]

    response = client.put(
        f"/api/admin/programas/{prog_id}",
        json={"titulo": "Updated Title", "referencia_archivo": "s3://b/updated.pdf"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["titulo"] == "Updated Title"
    assert data["referencia_archivo"] == "s3://b/updated.pdf"
    # Fields not sent should remain unchanged
    assert UUID(data["materia_id"])


@pytest.mark.asyncio
async def test_delete_programa_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/programas/{id} soft-deletes."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "DC1", "nombre": "Del Carrera"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "DELCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "DELMAT", "nombre": "Del Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/programas",
        json={
            "materia_id": mid, "carrera_id": cid, "cohorte_id": cohid,
            "titulo": "To Delete", "referencia_archivo": "s3://b/del.pdf",
        },
        headers=headers,
    )
    prog_id = create_resp.json()["id"]

    response = client.delete(f"/api/admin/programas/{prog_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone from list
    list_resp = client.get("/api/admin/programas", headers=headers)
    titulos = [p["titulo"] for p in list_resp.json()]
    assert "To Delete" not in titulos


@pytest.mark.asyncio
async def test_aislamiento_multi_tenant_programas(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Tenant isolation: Tenant A's programas not visible to Tenant B."""
    clear_all_caches()
    setup_a = await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@c17.test")

    # Tenant A creates a programa
    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "MTA", "nombre": "Tenant A Carrera"}, headers=headers_a
    )
    cid = c_resp.json()["id"]
    co_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "MTCOHA", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers_a,
    )
    coid = co_resp.json()["id"]
    m_resp = client.post(
        "/api/admin/materias", json={"codigo": "MTA", "nombre": "Materia TA"}, headers=headers_a
    )
    mid = m_resp.json()["id"]

    client.post(
        "/api/admin/programas",
        json={
            "materia_id": mid, "carrera_id": cid, "cohorte_id": coid,
            "titulo": "Solo TA", "referencia_archivo": "s3://b/ta.pdf",
        },
        headers=headers_a,
    )

    # Tenant B lists → should be empty
    resp = client.get("/api/admin/programas", headers=headers_b)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# ===================================================================
# FechaAcademica CRUD
# ===================================================================


@pytest.mark.asyncio
async def test_create_fecha_201(client: TestClient, db_session: AsyncSession) -> None:
    """POST /api/admin/fechas-academicas → 201."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "FC17", "nombre": "Fe Carrera"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "FECOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "FEMAT", "nombre": "Fe Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    response = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid,
            "cohorte_id": cohid,
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1C",
            "fecha": "2026-05-15",
            "titulo": "Primer Parcial",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Primer Parcial"
    assert data["tipo"] == "Parcial"
    assert data["numero"] == 1
    assert data["periodo"] == "2026-1C"
    assert data["fecha"] == "2026-05-15"
    assert UUID(data["id"])
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_fecha_tipo_invalido_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/fechas-academicas with invalid tipo → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "FC17B", "nombre": "Fe Carrera B"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "FECOHB", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "FEMATB", "nombre": "Fe Materia B"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    response = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid,
            "cohorte_id": cohid,
            "tipo": "NoExiste",
            "numero": 1,
            "periodo": "2026-1C",
            "fecha": "2026-05-15",
            "titulo": "Invalido",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_fecha_campos_extra_422(
    client: TestClient, db_session: AsyncSession
) -> None:
    """POST /api/admin/fechas-academicas with extra campos → 422."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    carrera_resp = client.post(
        "/api/admin/carreras", json={"codigo": "FC17C", "nombre": "Fe Carrera C"}, headers=headers
    )
    cid = carrera_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "FECOHC", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "FEMATC", "nombre": "Fe Materia C"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    response = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid,
            "cohorte_id": cohid,
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1C",
            "fecha": "2026-05-15",
            "titulo": "Extra",
            "campo_extra": "no deberia",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_fechas_con_filtros(
    client: TestClient, db_session: AsyncSession
) -> None:
    """GET /api/admin/fechas-academicas with filters."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "FLT1", "nombre": "Filtro Carrera"}, headers=headers
    )
    cid = c_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "FLTCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    m1_resp = client.post(
        "/api/admin/materias", json={"codigo": "FLT1", "nombre": "Filtro Mat 1"}, headers=headers
    )
    m1id = m1_resp.json()["id"]
    m2_resp = client.post(
        "/api/admin/materias", json={"codigo": "FLT2", "nombre": "Filtro Mat 2"}, headers=headers
    )
    m2id = m2_resp.json()["id"]

    # Create two fechas with same cohorte but different materia
    client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": m1id, "cohorte_id": cohid,
            "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-05-15",
            "titulo": "P1 M1",
        },
        headers=headers,
    )
    client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": m2id, "cohorte_id": cohid,
            "tipo": "TP", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-05-20",
            "titulo": "TP1 M2",
        },
        headers=headers,
    )

    # Filter by materia_id
    resp = client.get(f"/api/admin/fechas-academicas?materia_id={m1id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["titulo"] == "P1 M1"

    # Filter by tipo
    resp = client.get("/api/admin/fechas-academicas?tipo=TP", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["titulo"] == "TP1 M2"

    # Filter by cohorte_id
    resp = client.get(f"/api/admin/fechas-academicas?cohorte_id={cohid}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # No filter → all
    resp = client.get("/api/admin/fechas-academicas", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_fecha_200(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/fechas-academicas/{id} → 200."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "GETF1", "nombre": "Get Fe Carrera"}, headers=headers
    )
    cid = c_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "GETFCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "GETFMAT", "nombre": "Get Fe Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid, "cohorte_id": cohid,
            "tipo": "Coloquio", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-07-01",
            "titulo": "Coloquio Final",
        },
        headers=headers,
    )
    fid = create_resp.json()["id"]

    response = client.get(f"/api/admin/fechas-academicas/{fid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["titulo"] == "Coloquio Final"


@pytest.mark.asyncio
async def test_get_fecha_404(client: TestClient, db_session: AsyncSession) -> None:
    """GET /api/admin/fechas-academicas/{nonexistent} → 404."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    fake_id = "00000000-0000-0000-0000-000000000002"
    response = client.get(f"/api/admin/fechas-academicas/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert "no encontrad" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_fecha_200(client: TestClient, db_session: AsyncSession) -> None:
    """PUT /api/admin/fechas-academicas/{id} updates fields."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "UPF1", "nombre": "Upd Fe Carrera"}, headers=headers
    )
    cid = c_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "UPFCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "UPFMAT", "nombre": "Upd Fe Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid, "cohorte_id": cohid,
            "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-05-15",
            "titulo": "Original",
        },
        headers=headers,
    )
    fid = create_resp.json()["id"]

    response = client.put(
        f"/api/admin/fechas-academicas/{fid}",
        json={"titulo": "Actualizado", "fecha": "2026-06-01"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["titulo"] == "Actualizado"
    assert data["fecha"] == "2026-06-01"
    assert data["numero"] == 1  # unchanged


@pytest.mark.asyncio
async def test_delete_fecha_204(client: TestClient, db_session: AsyncSession) -> None:
    """DELETE /api/admin/fechas-academicas/{id} soft-deletes."""
    clear_all_caches()
    await _setup_admin(db_session)
    headers = await _auth_header(client)

    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "DELF1", "nombre": "Del Fe Carrera"}, headers=headers
    )
    cid = c_resp.json()["id"]
    coh_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "DELFCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers,
    )
    cohid = coh_resp.json()["id"]
    mat_resp = client.post(
        "/api/admin/materias", json={"codigo": "DELFMAT", "nombre": "Del Fe Materia"}, headers=headers
    )
    mid = mat_resp.json()["id"]

    create_resp = client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid, "cohorte_id": cohid,
            "tipo": "Recuperatorio", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-07-15",
            "titulo": "To Delete",
        },
        headers=headers,
    )
    fid = create_resp.json()["id"]

    response = client.delete(f"/api/admin/fechas-academicas/{fid}", headers=headers)
    assert response.status_code == 204

    list_resp = client.get("/api/admin/fechas-academicas", headers=headers)
    titulos = [f["titulo"] for f in list_resp.json()]
    assert "To Delete" not in titulos


@pytest.mark.asyncio
async def test_aislamiento_multi_tenant_fechas(
    client: TestClient, db_session: AsyncSession
) -> None:
    """Tenant isolation: Tenant A's fechas not visible to Tenant B."""
    clear_all_caches()
    setup_a = await _setup_admin(db_session)
    setup_b = await _setup_second_tenant(db_session)

    headers_a = await _auth_header(client)
    headers_b = await _auth_header(client, email="admin2@c17.test")

    c_resp = client.post(
        "/api/admin/carreras", json={"codigo": "MTFA", "nombre": "MT Fe A"}, headers=headers_a
    )
    cid = c_resp.json()["id"]
    co_resp = client.post(
        "/api/admin/cohortes",
        json={"carrera_id": cid, "nombre": "MTFCOH", "anio": 2026, "vig_desde": "2026-01-01"},
        headers=headers_a,
    )
    coid = co_resp.json()["id"]
    m_resp = client.post(
        "/api/admin/materias", json={"codigo": "MTFA", "nombre": "Materia Fe TA"}, headers=headers_a
    )
    mid = m_resp.json()["id"]

    client.post(
        "/api/admin/fechas-academicas",
        json={
            "materia_id": mid, "cohorte_id": coid,
            "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1C", "fecha": "2026-05-15",
            "titulo": "Solo TA",
        },
        headers=headers_a,
    )

    resp = client.get("/api/admin/fechas-academicas", headers=headers_b)
    assert resp.status_code == 200
    assert len(resp.json()) == 0
