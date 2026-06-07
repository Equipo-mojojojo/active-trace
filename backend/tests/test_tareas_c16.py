"""Tests for C-16: Tareas Internas.

Covers:
- Model creation, __repr__, enum values
- CRUD: create, list with filters, get detail, update estado
- Mis tareas: solo las del usuario autenticado
- Comentarios: agregar, listar, orden
- Permission guards: 403 without tareas:gestionar
- Multi-tenant isolation
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.comentario_tarea import ComentarioTarea
from app.models.enums import EstadoTarea
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tarea import Tarea
from tests.conftest import create_test_materia, create_test_tenant, create_test_user

_COORD_EMAIL = "coord@tareas.test"
_TUTOR_EMAIL = "tutor@tareas.test"
_SIN_PERM_EMAIL = "noperm@tareas.test"


async def _login(client: TestClient, email: str = _COORD_EMAIL) -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


async def _auth_header(client: TestClient, email: str = _COORD_EMAIL) -> dict:
    token = await _login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


async def _setup_base(db_session: AsyncSession) -> dict:
    tenant = await create_test_tenant(db_session)
    materia = await create_test_materia(db_session, tenant_id=tenant.id)

    role_coord = Role(tenant_id=tenant.id, nombre="COORDINADOR", editable=False)
    role_tutor = Role(tenant_id=tenant.id, nombre="TUTOR", editable=False)
    db_session.add_all([role_coord, role_tutor])
    await db_session.flush()

    perm_gestionar = Permission(
        tenant_id=tenant.id,
        codigo="tareas:gestionar",
        modulo="tareas",
        accion="gestionar",
    )
    db_session.add(perm_gestionar)
    await db_session.flush()

    rp1 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_coord.id,
        permiso_id=perm_gestionar.id,
    )
    db_session.add(rp1)
    await db_session.commit()

    coord = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_COORD_EMAIL,
        roles=["COORDINADOR"],
    )
    tutor = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_TUTOR_EMAIL,
        roles=["TUTOR"],
    )
    sin_perm = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_SIN_PERM_EMAIL,
        roles=["TUTOR"],
    )

    return {
        "tenant": tenant,
        "materia": materia,
        "coord": coord,
        "tutor": tutor,
        "sin_perm": sin_perm,
    }


@pytest_asyncio.fixture
async def base_setup(db_session: AsyncSession) -> dict:
    result = await _setup_base(db_session)
    return result


# ===================================================================
# 7.1: Tests de modelos
# ===================================================================


@pytest.mark.asyncio
async def test_estado_tarea_enum_values():
    assert EstadoTarea.PENDIENTE == "Pendiente"
    assert EstadoTarea.EN_PROGRESO == "En progreso"
    assert EstadoTarea.RESUELTA == "Resuelta"
    assert EstadoTarea.CANCELADA == "Cancelada"


@pytest.mark.asyncio
async def test_tarea_creation(db_session: AsyncSession, base_setup: dict):
    tarea = Tarea(
        tenant_id=base_setup["tenant"].id,
        asignado_a=base_setup["tutor"].id,
        asignado_por=base_setup["coord"].id,
        descripcion="Revisar entrega de TP",
    )
    db_session.add(tarea)
    await db_session.flush()

    assert tarea.id is not None
    assert tarea.estado == EstadoTarea.PENDIENTE
    assert tarea.descripcion == "Revisar entrega de TP"
    assert tarea.materia_id is None
    assert "Tarea" in repr(tarea)


@pytest.mark.asyncio
async def test_comentario_tarea_creation(db_session: AsyncSession, base_setup: dict):
    tarea = Tarea(
        tenant_id=base_setup["tenant"].id,
        asignado_a=base_setup["tutor"].id,
        asignado_por=base_setup["coord"].id,
        descripcion="Tarea test",
    )
    db_session.add(tarea)
    await db_session.flush()

    comentario = ComentarioTarea(
        tenant_id=base_setup["tenant"].id,
        tarea_id=tarea.id,
        autor_id=base_setup["coord"].id,
        texto="Revisado, falta corregir",
    )
    db_session.add(comentario)
    await db_session.flush()

    assert comentario.id is not None
    assert comentario.tarea_id == tarea.id
    assert comentario.creado_at is not None
    assert "ComentarioTarea" in repr(comentario)


# ===================================================================
# 7.2: Tests de CRUD
# ===================================================================


@pytest.mark.asyncio
async def test_create_tarea(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Revisar informes de laboratorio",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["descripcion"] == "Revisar informes de laboratorio"
    assert data["estado"] == "Pendiente"
    assert data["asignado_por"] == str(base_setup["coord"].id)
    assert data["asignado_a"] == str(base_setup["tutor"].id)


@pytest.mark.asyncio
async def test_create_tarea_con_materia(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Preparar clase",
            "materia_id": str(base_setup["materia"].id),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["materia_id"] == str(base_setup["materia"].id)


@pytest.mark.asyncio
async def test_list_tareas(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Tarea 1",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["coord"].id),
            "descripcion": "Tarea 2",
        },
        headers=headers,
    )

    resp = client.get("/api/v1/tareas", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_tareas_filtro_estado(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Pendiente",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Resuelta",
        },
        headers=headers,
    )

    resp = client.get(
        "/api/v1/tareas?estado=Pendiente",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["estado"] == "Pendiente" for t in data)


@pytest.mark.asyncio
async def test_get_tarea_detail(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Detalle test",
        },
        headers=headers,
    )
    tarea_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/tareas/{tarea_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["descripcion"] == "Detalle test"
    assert data["id"] == tarea_id


@pytest.mark.asyncio
async def test_update_tarea_estado(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Actualizable",
        },
        headers=headers,
    )
    tarea_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/tareas/{tarea_id}",
        json={"estado": "En progreso"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "En progreso"
    assert data["descripcion"] == "Actualizable"


@pytest.mark.asyncio
async def test_update_tarea_descripcion(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Original",
        },
        headers=headers,
    )
    tarea_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/tareas/{tarea_id}",
        json={"descripcion": "Modificada"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["descripcion"] == "Modificada"


# ===================================================================
# 7.3: Tests de mis-tareas
# ===================================================================


@pytest.mark.asyncio
async def test_mis_tareas_solo_del_usuario(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    tutor_headers = await _auth_header(client, email=_TUTOR_EMAIL)

    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Tarea del tutor",
        },
        headers=coord_headers,
    )
    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["coord"].id),
            "descripcion": "Tarea del coordinador",
        },
        headers=coord_headers,
    )

    resp_tutor = client.get("/api/v1/tareas/mias", headers=tutor_headers)
    assert resp_tutor.status_code == 200
    data_tutor = resp_tutor.json()
    assert len(data_tutor) == 1
    assert data_tutor[0]["descripcion"] == "Tarea del tutor"

    resp_coord = client.get("/api/v1/tareas/mias", headers=coord_headers)
    assert resp_coord.status_code == 200
    assert len(resp_coord.json()) == 1
    assert resp_coord.json()[0]["descripcion"] == "Tarea del coordinador"


# ===================================================================
# 7.4: Tests de comentarios
# ===================================================================


@pytest.mark.asyncio
async def test_agregar_comentario(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Tarea con comentario",
        },
        headers=headers,
    )
    tarea_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        json={"texto": "Primer comentario"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["texto"] == "Primer comentario"
    assert data["tarea_id"] == tarea_id
    assert data["autor_id"] == str(base_setup["coord"].id)


@pytest.mark.asyncio
async def test_listar_comentarios_orden(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Tarea varios comentarios",
        },
        headers=headers,
    )
    tarea_id = create_resp.json()["id"]

    client.post(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        json={"texto": "Primero"},
        headers=headers,
    )
    client.post(
        f"/api/v1/tareas/{tarea_id}/comentarios",
        json={"texto": "Segundo"},
        headers=headers,
    )

    resp = client.get(f"/api/v1/tareas/{tarea_id}/comentarios", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["texto"] == "Primero"
    assert data[1]["texto"] == "Segundo"


@pytest.mark.asyncio
async def test_comentario_tarea_inexistente_da_404(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    fake_id = str(uuid4())
    resp = client.post(
        f"/api/v1/tareas/{fake_id}/comentarios",
        json={"texto": "No existe"},
        headers=headers,
    )
    assert resp.status_code == 404


# ===================================================================
# 7.5: Tests de permisos
# ===================================================================


@pytest.mark.asyncio
async def test_list_tareas_sin_permiso_da_403(client: TestClient, base_setup: dict):
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)
    resp = client.get("/api/v1/tareas", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_tarea_sin_permiso_da_403(client: TestClient, base_setup: dict):
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)
    resp = client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "No deberia crear",
        },
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mis_tareas_sin_auth_da_401(client: TestClient):
    resp = client.get("/api/v1/tareas/mias")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_mis_tareas_sin_permiso_ok(client: TestClient, base_setup: dict):
    """Cualquier user autenticado puede ver sus tareas, sin permiso especial."""
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)
    resp = client.get("/api/v1/tareas/mias", headers=headers)
    assert resp.status_code == 200


# ===================================================================
# 7.6: Tests de aislamiento multi-tenant
# ===================================================================


@pytest.mark.asyncio
async def test_multi_tenant_aislamiento_tareas(
    client: TestClient,
    db_session: AsyncSession,
    base_setup: dict,
):
    headers_a = await _auth_header(client)

    client.post(
        "/api/v1/tareas",
        json={
            "asignado_a": str(base_setup["tutor"].id),
            "descripcion": "Tarea Tenant A",
        },
        headers=headers_a,
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")
    role_b = Role(tenant_id=tenant_b.id, nombre="COORDINADOR", editable=False)
    db_session.add(role_b)
    await db_session.flush()

    perm_b = Permission(
        tenant_id=tenant_b.id,
        codigo="tareas:gestionar",
        modulo="tareas",
        accion="gestionar",
    )
    db_session.add(perm_b)
    await db_session.flush()

    db_session.add(
        RolePermission(
            tenant_id=tenant_b.id,
            rol_id=role_b.id,
            permiso_id=perm_b.id,
        )
    )
    await db_session.commit()
    clear_all_caches()

    user_b = await create_test_user(
        db_session,
        tenant_id=tenant_b.id,
        email="coord_b@tareas.test",
        roles=["COORDINADOR"],
    )
    await db_session.commit()
    clear_all_caches()

    resp_b_login = client.post(
        "/api/auth/login",
        json={"email": "coord_b@tareas.test", "password": "Password123!"},
    )
    assert resp_b_login.status_code == 200
    token_b = resp_b_login.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_b = client.get("/api/v1/tareas", headers=headers_b)
    assert resp_b.status_code == 200
    assert len(resp_b.json()) == 0

    resp_a = client.get("/api/v1/tareas", headers=headers_a)
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
