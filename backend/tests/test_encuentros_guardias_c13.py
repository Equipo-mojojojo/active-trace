"""Tests for C-13: Encuentros y Guardias.

Covers:
- SlotEncuentro: recurrente con generación de instancias, fecha única, CRUD
- InstanciaEncuentro: CRUD, cambios de estado, video_url validation
- Guardia: CRUD, export CSV
- EncuentroExportService: generación de HTML
- Multi-tenant isolation
- Permission guards
"""

from __future__ import annotations

from datetime import date, time
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.enums import DiaSemana, EstadoEncuentro, EstadoGuardia
from app.models.guardia import Guardia
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.slot_encuentro import SlotEncuentro
from app.services.encuentro_export_service import EncuentroExportService
from app.services.guardia_service import GuardiaService
from app.services.instancia_encuentro_service import (
    InstanciaEncuentroService,
)
from app.services.slot_encuentro_service import SlotEncuentroService
from tests.conftest import (
    create_test_materia,
    create_test_tenant,
    create_test_user,
    create_test_usuario_docente,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_PROFESOR_EMAIL = "prof@encuentros.test"
_TUTOR_EMAIL = "tutor@encuentros.test"
_SIN_PERM_EMAIL = "noperm@encuentros.test"


# ===================================================================
# Helpers
# ===================================================================


async def _login(client: TestClient, email: str = _PROFESOR_EMAIL) -> str:
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


async def _auth_header(client: TestClient, email: str = _PROFESOR_EMAIL) -> dict:
    token = await _login(client, email=email)
    return {"Authorization": f"Bearer {token}"}


async def _setup_base(db_session: AsyncSession) -> dict:
    """Seed tenant + roles + permissions + users."""
    tenant = await create_test_tenant(db_session)
    materia = await create_test_materia(db_session, tenant_id=tenant.id)

    role_prof = Role(tenant_id=tenant.id, nombre="PROFESOR", editable=False)
    role_tutor = Role(tenant_id=tenant.id, nombre="TUTOR", editable=False)
    db_session.add_all([role_prof, role_tutor])
    await db_session.flush()

    perm_gestionar = Permission(
        tenant_id=tenant.id,
        codigo="encuentros:gestionar",
        modulo="encuentros",
        accion="gestionar",
    )
    perm_ver = Permission(
        tenant_id=tenant.id,
        codigo="encuentros:ver",
        modulo="encuentros",
        accion="ver",
    )
    perm_guardias = Permission(
        tenant_id=tenant.id,
        codigo="guardias:registrar",
        modulo="guardias",
        accion="registrar",
    )
    db_session.add_all([perm_gestionar, perm_ver, perm_guardias])
    await db_session.flush()

    rp1 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_prof.id,
        permiso_id=perm_gestionar.id,
    )
    rp2 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_prof.id,
        permiso_id=perm_ver.id,
    )
    rp3 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_tutor.id,
        permiso_id=perm_ver.id,
    )
    rp4 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_tutor.id,
        permiso_id=perm_guardias.id,
    )
    db_session.add_all([rp1, rp2, rp3, rp4])
    await db_session.commit()

    profesor = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=_PROFESOR_EMAIL,
        roles=["PROFESOR"],
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
        roles=["ALUMNO"],
    )

    usuario_docente = await create_test_usuario_docente(
        db_session,
        tenant_id=tenant.id,
        nombre="Prof",
        apellidos="Tester",
        email="prof@dominio.test",
    )

    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte

    carrera = Carrera(
        tenant_id=tenant.id, codigo="CARR-TEST", nombre="Carrera Test"
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="COH-TEST",
        anio=2026,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(cohorte)
    await db_session.flush()

    return {
        "tenant": tenant,
        "materia": materia,
        "profesor": profesor,
        "tutor": tutor,
        "sin_perm": sin_perm,
        "usuario_docente": usuario_docente,
        "carrera": carrera,
        "cohorte": cohorte,
    }


@pytest_asyncio.fixture
async def base_setup(db_session: AsyncSession) -> dict:
    result = await _setup_base(db_session)
    return result


# ===================================================================
# 7.1: Tests de modelos
# ===================================================================


@pytest.mark.asyncio
async def test_slot_encuentro_creation(db_session: AsyncSession, base_setup: dict):
    slot = SlotEncuentro(
        tenant_id=base_setup["tenant"].id,
        asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
        materia_id=base_setup["materia"].id,
        titulo="Clase 1",
        hora=time(18, 0),
        dia_semana=DiaSemana.LUNES,
        fecha_inicio=date(2026, 3, 2),
        cant_semanas=4,
        meet_url="https://meet.example.com/clase1",
        vig_desde=date(2026, 3, 1),
    )
    db_session.add(slot)
    await db_session.flush()

    assert slot.id is not None
    assert slot.titulo == "Clase 1"
    assert slot.dia_semana == DiaSemana.LUNES
    assert "SlotEncuentro" in repr(slot)


@pytest.mark.asyncio
async def test_instancia_encuentro_creation(db_session: AsyncSession, base_setup: dict):
    instancia = InstanciaEncuentro(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        fecha=date(2026, 3, 2),
        hora=time(18, 0),
        titulo="Clase 1 - Semana 1",
        estado=EstadoEncuentro.PROGRAMADO,
    )
    db_session.add(instancia)
    await db_session.flush()

    assert instancia.id is not None
    assert instancia.estado == EstadoEncuentro.PROGRAMADO
    assert "InstanciaEncuentro" in repr(instancia)


@pytest.mark.asyncio
async def test_guardia_creation(db_session: AsyncSession, base_setup: dict):
    guardia = Guardia(
        tenant_id=base_setup["tenant"].id,
        asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
        materia_id=base_setup["materia"].id,
        carrera_id=base_setup["carrera"].id,
        cohorte_id=base_setup["cohorte"].id,
        dia=DiaSemana.MARTES,
        horario="14:00–14:45",
        estado=EstadoGuardia.PENDIENTE,
    )
    db_session.add(guardia)
    await db_session.flush()

    assert guardia.id is not None
    assert guardia.estado == EstadoGuardia.PENDIENTE
    assert "Guardia" in repr(guardia)


# ===================================================================
# 7.2 & 7.3: Slot recurrente y fecha única
# ===================================================================


@pytest.mark.asyncio
async def test_slot_recurrente_genera_instancias(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import SlotEncuentroCreate

    service = SlotEncuentroService(db_session, base_setup["tenant"].id)
    slot_data = SlotEncuentroCreate(
        asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
        materia_id=base_setup["materia"].id,
        titulo="Clase Recurrente",
        hora=time(18, 0),
        dia_semana="Lunes",
        fecha_inicio=date(2026, 3, 2),
        cant_semanas=4,
        vig_desde=date(2026, 3, 1),
    )
    slot = await service.create(slot_data)
    assert slot.id is not None

    inst_service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancias = await inst_service.list(slot_id=slot.id)
    assert len(instancias) == 4
    assert instancias[0].fecha == date(2026, 3, 2)
    assert instancias[3].fecha == date(2026, 3, 23)


@pytest.mark.asyncio
async def test_slot_fecha_unica_genera_una_instancia(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import SlotEncuentroCreate

    service = SlotEncuentroService(db_session, base_setup["tenant"].id)
    slot_data = SlotEncuentroCreate(
        asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
        materia_id=base_setup["materia"].id,
        titulo="Clase Única",
        hora=time(10, 0),
        dia_semana="Miércoles",
        fecha_inicio=date(2026, 4, 15),
        cant_semanas=0,
        fecha_unica=date(2026, 4, 15),
        vig_desde=date(2026, 4, 1),
    )
    slot = await service.create(slot_data)
    inst_service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancias = await inst_service.list(slot_id=slot.id)
    assert len(instancias) == 1
    assert instancias[0].fecha == date(2026, 4, 15)


@pytest.mark.asyncio
async def test_slot_soft_delete(db_session: AsyncSession, base_setup: dict):
    from app.schemas.encuentros import SlotEncuentroCreate

    service = SlotEncuentroService(db_session, base_setup["tenant"].id)
    slot_data = SlotEncuentroCreate(
        asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
        materia_id=base_setup["materia"].id,
        titulo="Slot a eliminar",
        hora=time(18, 0),
        dia_semana="Viernes",
        fecha_inicio=date(2026, 5, 1),
        cant_semanas=2,
        vig_desde=date(2026, 5, 1),
    )
    slot = await service.create(slot_data)

    inst_service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancias_before = await inst_service.list(slot_id=slot.id)
    assert len(instancias_before) == 2

    await service.delete(slot.id)

    deleted_slot = await service.repository.get_by_id(slot.id, include_deleted=True)
    assert deleted_slot.deleted_at is not None

    instancias_after = await inst_service.list(slot_id=slot.id)
    assert len(instancias_after) == 2


# ===================================================================
# 7.4: Tests de instancias
# ===================================================================


@pytest.mark.asyncio
async def test_crear_instancia_independiente(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import InstanciaEncuentroCreate

    service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    data = InstanciaEncuentroCreate(
        materia_id=base_setup["materia"].id,
        fecha=date(2026, 6, 1),
        hora=time(14, 0),
        titulo="Encuentro único",
    )
    instancia = await service.create(data)
    assert instancia.titulo == "Encuentro único"
    assert instancia.estado == EstadoEncuentro.PROGRAMADO
    assert instancia.slot_id is None


@pytest.mark.asyncio
async def test_actualizar_estado_a_realizado(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import InstanciaEncuentroCreate, InstanciaEncuentroUpdate

    service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancia = await service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 6, 1),
            hora=time(14, 0),
            titulo="Test",
        )
    )
    updated = await service.update(
        instancia.id,
        InstanciaEncuentroUpdate(
            estado="Realizado",
            video_url="https://ejemplo.com/grabacion",
        ),
    )
    assert updated.estado == EstadoEncuentro.REALIZADO
    assert updated.video_url == "https://ejemplo.com/grabacion"


@pytest.mark.asyncio
async def test_video_url_rechazado_sin_realizado(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import InstanciaEncuentroCreate, InstanciaEncuentroUpdate
    from fastapi import HTTPException

    service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancia = await service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 6, 1),
            hora=time(14, 0),
            titulo="Test video sin realizado",
        )
    )
    with pytest.raises(HTTPException) as exc:
        await service.update(
            instancia.id,
            InstanciaEncuentroUpdate(video_url="https://ejemplo.com/grabacion"),
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_instancia_cancelar(db_session: AsyncSession, base_setup: dict):
    from app.schemas.encuentros import InstanciaEncuentroCreate, InstanciaEncuentroUpdate

    service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    instancia = await service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 6, 1),
            hora=time(14, 0),
            titulo="A cancelar",
        )
    )
    updated = await service.update(
        instancia.id,
        InstanciaEncuentroUpdate(estado="Cancelado"),
    )
    assert updated.estado == EstadoEncuentro.CANCELADO


@pytest.mark.asyncio
async def test_listar_instancias_con_filtros(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import InstanciaEncuentroCreate

    service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    await service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 3, 1),
            hora=time(10, 0),
            titulo="Marzo",
        )
    )
    await service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 4, 1),
            hora=time(10, 0),
            titulo="Abril",
        )
    )
    result = await service.list(
        materia_id=base_setup["materia"].id,
        desde=date(2026, 3, 1),
        hasta=date(2026, 3, 31),
    )
    assert len(result) == 1
    assert result[0].titulo == "Marzo"


# ===================================================================
# 7.5: Tests de guardias
# ===================================================================


@pytest.mark.asyncio
async def test_crear_guardia(db_session: AsyncSession, base_setup: dict):
    from app.schemas.guardias import GuardiaCreate

    service = GuardiaService(db_session, base_setup["tenant"].id)
    guardia = await service.create(
        GuardiaCreate(
            asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
            materia_id=base_setup["materia"].id,
            carrera_id=base_setup["carrera"].id,
            cohorte_id=base_setup["cohorte"].id,
            dia="Lunes",
            horario="14:00–14:45",
        )
    )
    assert guardia.estado == EstadoGuardia.PENDIENTE


@pytest.mark.asyncio
async def test_editar_guardia(db_session: AsyncSession, base_setup: dict):
    from app.schemas.guardias import GuardiaCreate, GuardiaUpdate

    service = GuardiaService(db_session, base_setup["tenant"].id)
    guardia = await service.create(
        GuardiaCreate(
            asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
            materia_id=base_setup["materia"].id,
            carrera_id=base_setup["carrera"].id,
            cohorte_id=base_setup["cohorte"].id,
            dia="Martes",
            horario="15:00–15:45",
        )
    )
    updated = await service.update(
        guardia.id,
        GuardiaUpdate(estado="Realizada", comentarios="Todo OK"),
    )
    assert updated.estado == EstadoGuardia.REALIZADA
    assert updated.comentarios == "Todo OK"


@pytest.mark.asyncio
async def test_listar_guardias_filtradas(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.guardias import GuardiaCreate

    service = GuardiaService(db_session, base_setup["tenant"].id)
    await service.create(
        GuardiaCreate(
            asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
            materia_id=base_setup["materia"].id,
            carrera_id=base_setup["carrera"].id,
            cohorte_id=base_setup["cohorte"].id,
            dia="Lunes",
            horario="14:00–14:45",
        )
    )
    result = await service.list(materia_id=base_setup["materia"].id)
    assert len(result) == 1

    result_empty = await service.list(
        materia_id=UUID("00000000-0000-0000-0000-000000000099")
    )
    assert len(result_empty) == 0


# ===================================================================
# 7.6: Tests de export HTML
# ===================================================================


@pytest.mark.asyncio
async def test_generar_html_con_instancias(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import InstanciaEncuentroCreate, InstanciaEncuentroUpdate

    inst_service = InstanciaEncuentroService(db_session, base_setup["tenant"].id)
    await inst_service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 3, 2),
            hora=time(18, 0),
            titulo="Clase 1",
        )
    )
    await inst_service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 3, 9),
            hora=time(18, 0),
            titulo="Clase 2",
        )
    )
    inst3 = await inst_service.create(
        InstanciaEncuentroCreate(
            materia_id=base_setup["materia"].id,
            fecha=date(2026, 3, 16),
            hora=time(18, 0),
            titulo="Clase cancelada",
        )
    )
    # Cancel and then realize with video
    await inst_service.update(
        inst3.id,
        InstanciaEncuentroUpdate(estado="Cancelado"),
    )
    await inst_service.update(
        inst3.id,
        InstanciaEncuentroUpdate(
            estado="Realizado",
            video_url="https://ejemplo.com/grabacion",
        ),
    )

    export_service = EncuentroExportService(db_session, base_setup["tenant"].id)
    result = await export_service.generate_html(base_setup["materia"].id)

    assert "Clase 1" in result.html
    assert "Clase 2" in result.html
    assert "Calendario" in result.html
    assert result.materia_nombre == base_setup["materia"].nombre


@pytest.mark.asyncio
async def test_generar_html_sin_instancias(
    db_session: AsyncSession, base_setup: dict
):
    export_service = EncuentroExportService(db_session, base_setup["tenant"].id)
    result = await export_service.generate_html(base_setup["materia"].id)
    assert "No hay encuentros programados" in result.html


# ===================================================================
# 7.7: Tests de permisos (API)
# ===================================================================


@pytest.mark.asyncio
async def test_slot_sin_permiso_403(client: TestClient, db_session: AsyncSession):
    clear_all_caches()
    await _setup_base(db_session)
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)

    response = client.get("/api/v1/encuentros/slots", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_guardia_sin_permiso_403(client: TestClient, db_session: AsyncSession):
    clear_all_caches()
    await _setup_base(db_session)
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)

    response = client.get("/api/v1/guardias", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_profesor_puede_crear_slot(
    client: TestClient, db_session: AsyncSession
):
    clear_all_caches()
    setup = await _setup_base(db_session)
    headers = await _auth_header(client, email=_PROFESOR_EMAIL)

    payload = {
        "asignacion_id": "00000000-0000-0000-0000-000000000001",
        "materia_id": str(setup["materia"].id),
        "titulo": "Clase desde API",
        "hora": "18:00:00",
        "dia_semana": "Lunes",
        "fecha_inicio": "2026-03-02",
        "cant_semanas": 2,
        "vig_desde": "2026-03-01",
    }
    response = client.post(
        "/api/v1/encuentros/slots",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Clase desde API"


# ===================================================================
# 7.8: Tests de aislamiento multi-tenant
# ===================================================================


@pytest.mark.asyncio
async def test_slots_aislados_por_tenant(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.encuentros import SlotEncuentroCreate

    service_a = SlotEncuentroService(db_session, base_setup["tenant"].id)
    await service_a.create(
        SlotEncuentroCreate(
            asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
            materia_id=base_setup["materia"].id,
            titulo="Slot tenant A",
            hora=time(18, 0),
            dia_semana="Lunes",
            fecha_inicio=date(2026, 3, 2),
            cant_semanas=1,
            vig_desde=date(2026, 3, 1),
        )
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")
    service_b = SlotEncuentroService(db_session, tenant_b.id)
    slots_b = await service_b.list()
    assert len(slots_b) == 0


@pytest.mark.asyncio
async def test_guardias_aisladas_por_tenant(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.guardias import GuardiaCreate

    service_a = GuardiaService(db_session, base_setup["tenant"].id)
    await service_a.create(
        GuardiaCreate(
            asignacion_id=UUID("00000000-0000-0000-0000-000000000001"),
            materia_id=base_setup["materia"].id,
            carrera_id=base_setup["carrera"].id,
            cohorte_id=base_setup["cohorte"].id,
            dia="Lunes",
            horario="14:00–14:45",
        )
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")
    service_b = GuardiaService(db_session, tenant_b.id)
    guardias_b = await service_b.list()
    assert len(guardias_b) == 0
