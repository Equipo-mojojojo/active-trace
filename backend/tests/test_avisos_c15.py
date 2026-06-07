"""Tests for C-15: Avisos y Acknowledgment.

Covers:
- Aviso: CRUD, alcances, orden, activo/inactivo
- Acknowledgment: confirmar, idempotencia, validación
- Mis avisos: filtrado por alcance, vigencia, rol, exclusión de acked
- Contadores: total_acks, total_visibles
- Permission guards
- Multi-tenant isolation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.models.enums import AlcanceAviso, SeveridadAviso
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from tests.conftest import (
    create_test_materia,
    create_test_tenant,
    create_test_user,
    create_test_cohorte,
)

_COORD_EMAIL = "coord@avisos.test"
_ALUMNO_EMAIL = "alumno@avisos.test"
_ALUMNO2_EMAIL = "alumno2@avisos.test"
_SIN_PERM_EMAIL = "noperm@avisos.test"


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
    cohorte = await create_test_cohorte(db_session, tenant_id=tenant.id)

    role_coord = Role(tenant_id=tenant.id, nombre="COORDINADOR", editable=False)
    role_alumno = Role(tenant_id=tenant.id, nombre="ALUMNO", editable=False)
    db_session.add_all([role_coord, role_alumno])
    await db_session.flush()

    perm_publicar = Permission(
        tenant_id=tenant.id,
        codigo="avisos:publicar",
        modulo="avisos",
        accion="publicar",
    )
    db_session.add(perm_publicar)
    await db_session.flush()

    rp1 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_coord.id,
        permiso_id=perm_publicar.id,
    )
    db_session.add(rp1)
    await db_session.commit()

    coord = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_COORD_EMAIL,
        roles=["COORDINADOR"],
    )
    alumno = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_ALUMNO_EMAIL,
        roles=["ALUMNO"],
    )
    alumno2 = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_ALUMNO2_EMAIL,
        roles=["ALUMNO"],
    )
    sin_perm = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_SIN_PERM_EMAIL,
        roles=["ALUMNO"],
    )

    return {
        "tenant": tenant,
        "materia": materia,
        "cohorte": cohorte,
        "coord": coord,
        "alumno": alumno,
        "alumno2": alumno2,
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
async def test_aviso_creation(db_session: AsyncSession, base_setup: dict):
    aviso = Aviso(
        tenant_id=base_setup["tenant"].id,
        alcance=AlcanceAviso.GLOBAL,
        severidad=SeveridadAviso.INFO,
        titulo="Bienvenidos",
        cuerpo="Cuerpo del aviso",
        inicio_en=datetime.now(timezone.utc),
        orden=1,
    )
    db_session.add(aviso)
    await db_session.flush()

    assert aviso.id is not None
    assert aviso.alcance == AlcanceAviso.GLOBAL
    assert aviso.severidad == SeveridadAviso.INFO
    assert aviso.activo is True
    assert aviso.requiere_ack is False
    assert "Aviso" in repr(aviso)


@pytest.mark.asyncio
async def test_acknowledgment_creation(db_session: AsyncSession, base_setup: dict):
    aviso = Aviso(
        tenant_id=base_setup["tenant"].id,
        alcance=AlcanceAviso.GLOBAL,
        severidad=SeveridadAviso.INFO,
        titulo="Test",
        cuerpo="Cuerpo",
        inicio_en=datetime.now(timezone.utc),
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.flush()

    ack = AcknowledgmentAviso(
        tenant_id=base_setup["tenant"].id,
        aviso_id=aviso.id,
        usuario_id=base_setup["alumno"].id,
    )
    db_session.add(ack)
    await db_session.flush()

    assert ack.id is not None
    assert ack.aviso_id == aviso.id
    assert ack.confirmado_at is not None
    assert "AcknowledgmentAviso" in repr(ack)


@pytest.mark.asyncio
async def test_enums_values():
    assert AlcanceAviso.GLOBAL == "Global"
    assert AlcanceAviso.POR_MATERIA == "PorMateria"
    assert AlcanceAviso.POR_COHORTE == "PorCohorte"
    assert AlcanceAviso.POR_ROL == "PorRol"
    assert SeveridadAviso.INFO == "Info"
    assert SeveridadAviso.ADVERTENCIA == "Advertencia"
    assert SeveridadAviso.CRITICO == "Crítico"


# ===================================================================
# 7.2: Tests de CRUD de avisos
# ===================================================================


@pytest.mark.asyncio
async def test_create_aviso_global(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso Global",
            "cuerpo": "Contenido del aviso global",
            "inicio_en": "2026-01-01T00:00:00Z",
            "orden": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["titulo"] == "Aviso Global"
    assert data["alcance"] == "Global"
    assert data["activo"] is True


@pytest.mark.asyncio
async def test_create_aviso_por_materia(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "PorMateria",
            "severidad": "Advertencia",
            "titulo": "Aviso x Materia",
            "cuerpo": "Solo para una materia",
            "materia_id": str(base_setup["materia"].id),
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["alcance"] == "PorMateria"
    assert data["materia_id"] == str(base_setup["materia"].id)


@pytest.mark.asyncio
async def test_list_avisos(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso 1",
            "cuerpo": "Cuerpo",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Critico",
            "titulo": "Aviso 2",
            "cuerpo": "Cuerpo",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )

    resp = client.get("/api/v1/avisos", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_update_aviso(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Original",
            "cuerpo": "Cuerpo original",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )
    aviso_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/avisos/{aviso_id}",
        json={"titulo": "Actualizado", "activo": False},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["titulo"] == "Actualizado"
    assert data["activo"] is False


@pytest.mark.asyncio
async def test_get_aviso_detail(client: TestClient, base_setup: dict):
    headers = await _auth_header(client)
    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Detalle test",
            "cuerpo": "Cuerpo",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )
    aviso_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/avisos/{aviso_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["titulo"] == "Detalle test"
    assert "total_acks" in data
    assert "total_visibles" in data


# ===================================================================
# 7.3: Tests de visualización filtrada (mis-avisos)
# ===================================================================


@pytest.mark.asyncio
async def test_mis_avisos_global(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso Global",
            "cuerpo": "Para todos",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=coord_headers,
    )

    resp = client.get("/api/v1/avisos/mis-avisos", headers=alumno_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["titulo"] == "Aviso Global"


@pytest.mark.asyncio
async def test_mis_avisos_fuera_ventana_excluido(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    past = datetime.now(timezone.utc) - timedelta(days=10)
    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Vencido",
            "cuerpo": "Ya venció",
            "inicio_en": past.isoformat(),
            "fin_en": (past + timedelta(hours=1)).isoformat(),
        },
        headers=coord_headers,
    )

    resp = client.get("/api/v1/avisos/mis-avisos", headers=alumno_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_mis_avisos_por_rol(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "PorRol",
            "severidad": "Info",
            "titulo": "Solo alumnos",
            "cuerpo": "Mensaje",
            "rol_destino": "ALUMNO",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=coord_headers,
    )
    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "PorRol",
            "severidad": "Info",
            "titulo": "Solo admins",
            "cuerpo": "Mensaje",
            "rol_destino": "ADMIN",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=coord_headers,
    )

    resp = client.get("/api/v1/avisos/mis-avisos", headers=alumno_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["titulo"] == "Solo alumnos"


# ===================================================================
# 7.4: Tests de acknowledgment
# ===================================================================


@pytest.mark.asyncio
async def test_confirmar_ack(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Requiere ack",
            "cuerpo": "Confirmame",
            "inicio_en": "2026-01-01T00:00:00Z",
            "requiere_ack": True,
        },
        headers=coord_headers,
    )
    aviso_id = create_resp.json()["id"]

    resp = client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["aviso_id"] == aviso_id
    assert data["usuario_id"] == str(base_setup["alumno"].id)


@pytest.mark.asyncio
async def test_ack_idempotente(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Idempotente",
            "cuerpo": "Confirmame dos veces",
            "inicio_en": "2026-01-01T00:00:00Z",
            "requiere_ack": True,
        },
        headers=coord_headers,
    )
    aviso_id = create_resp.json()["id"]

    resp1 = client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)
    assert resp1.status_code == 200

    resp2 = client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)
    assert resp2.status_code == 200
    assert resp2.json()["id"] == resp1.json()["id"]


@pytest.mark.asyncio
async def test_ack_sin_requisito_da_400(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "No requiere ack",
            "cuerpo": "No hace falta confirmar",
            "inicio_en": "2026-01-01T00:00:00Z",
            "requiere_ack": False,
        },
        headers=coord_headers,
    )
    aviso_id = create_resp.json()["id"]

    resp = client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ack_excluye_de_mis_avisos(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Ack y desaparece",
            "cuerpo": "Luego de confirmar no se ve",
            "inicio_en": "2026-01-01T00:00:00Z",
            "requiere_ack": True,
        },
        headers=coord_headers,
    )
    aviso_id = create_resp.json()["id"]

    resp1 = client.get("/api/v1/avisos/mis-avisos", headers=alumno_headers)
    assert resp1.status_code == 200
    assert len(resp1.json()) == 1

    client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)

    resp2 = client.get("/api/v1/avisos/mis-avisos", headers=alumno_headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


# ===================================================================
# 7.5: Tests de contadores
# ===================================================================


@pytest.mark.asyncio
async def test_detail_contiene_total_acks(client: TestClient, base_setup: dict):
    coord_headers = await _auth_header(client)
    alumno_headers = await _auth_header(client, email=_ALUMNO_EMAIL)
    alumno2_headers = await _auth_header(client, email=_ALUMNO2_EMAIL)

    create_resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Contar acks",
            "cuerpo": "Test",
            "inicio_en": "2026-01-01T00:00:00Z",
            "requiere_ack": True,
        },
        headers=coord_headers,
    )
    aviso_id = create_resp.json()["id"]

    detail_resp = client.get(f"/api/v1/avisos/{aviso_id}", headers=coord_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["total_acks"] == 0

    client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno_headers)
    client.post(f"/api/v1/avisos/{aviso_id}/ack", headers=alumno2_headers)

    detail_resp = client.get(f"/api/v1/avisos/{aviso_id}", headers=coord_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["total_acks"] == 2


# ===================================================================
# 7.6: Tests de permisos
# ===================================================================


@pytest.mark.asyncio
async def test_list_avisos_sin_permiso_da_403(client: TestClient, base_setup: dict):
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)
    resp = client.get("/api/v1/avisos", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_aviso_sin_permiso_da_403(client: TestClient, base_setup: dict):
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)
    resp = client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "No deberia",
            "cuerpo": "No creado",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mis_avisos_sin_auth_da_401(client: TestClient, base_setup: dict):
    resp = client.get("/api/v1/avisos/mis-avisos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ack_sin_auth_da_401(client: TestClient, base_setup: dict):
    resp = client.post(f"/api/v1/avisos/{uuid4()}/ack")
    assert resp.status_code == 401


# ===================================================================
# 7.7: Tests de aislamiento multi-tenant
# ===================================================================


@pytest.mark.asyncio
async def test_multi_tenant_aislamiento_avisos(
    client: TestClient,
    db_session: AsyncSession,
    base_setup: dict,
):
    headers_a = await _auth_header(client)

    client.post(
        "/api/v1/avisos",
        json={
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Aviso Tenant A",
            "cuerpo": "Solo tenant A",
            "inicio_en": "2026-01-01T00:00:00Z",
        },
        headers=headers_a,
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")
    role_b = Role(tenant_id=tenant_b.id, nombre="COORDINADOR", editable=False)
    db_session.add(role_b)
    await db_session.flush()

    perm_b = Permission(
        tenant_id=tenant_b.id,
        codigo="avisos:publicar",
        modulo="avisos",
        accion="publicar",
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
        email="coord_b@avisos.test",
        roles=["COORDINADOR"],
    )
    await db_session.commit()
    clear_all_caches()

    resp_b_login = client.post(
        "/api/auth/login",
        json={"email": "coord_b@avisos.test", "password": "Password123!"},
    )
    assert resp_b_login.status_code == 200
    token_b = resp_b_login.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_b = client.get("/api/v1/avisos", headers=headers_b)
    assert resp_b.status_code == 200
    assert len(resp_b.json()) == 0

    resp_a = client.get("/api/v1/avisos", headers=headers_a)
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
