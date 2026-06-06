"""Tests for C-14: Evaluaciones y Coloquios.

Covers:
- Evaluacion: CRUD con turnos, cierre
- Convocado: import, list, remove, duplicates
- Reserva: book, cupo validation, convocado validation, cancel
- Resultado: register, update, list, export CSV
- Metricas: global and per-convocatoria
- Permission guards
- Multi-tenant isolation
"""

from __future__ import annotations

from datetime import date, time
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import clear_all_caches
from app.models.enums import (
    EstadoEvaluacion,
    EstadoReserva,
    TipoEvaluacion,
)
from app.models.evaluacion import Evaluacion
from app.models.turno_evaluacion import TurnoEvaluacion
from app.models.convocado import Convocado
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.services.evaluacion_service import EvaluacionService
from app.services.convocado_service import ConvocadoService
from app.services.reserva_service import ReservaService
from app.services.resultado_service import ResultadoService
from app.services.metricas_service import MetricasService
from tests.conftest import (
    create_test_materia,
    create_test_tenant,
    create_test_user,
    create_test_cohorte,
)

_COORD_EMAIL = "coord@coloquios.test"
_ALUMNO_EMAIL = "alumno@coloquios.test"
_ALUMNO2_EMAIL = "alumno2@coloquios.test"
_SIN_PERM_EMAIL = "noperm@coloquios.test"

_TURNO_IDS: list[UUID] = []


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

    perm_gestionar = Permission(
        tenant_id=tenant.id,
        codigo="coloquios:gestionar",
        modulo="coloquios",
        accion="gestionar",
    )
    perm_ver = Permission(
        tenant_id=tenant.id,
        codigo="coloquios:ver",
        modulo="coloquios",
        accion="ver",
    )
    perm_reservar = Permission(
        tenant_id=tenant.id,
        codigo="coloquios:reservar",
        modulo="coloquios",
        accion="reservar",
    )
    db_session.add_all([perm_gestionar, perm_ver, perm_reservar])
    await db_session.flush()

    rp1 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_coord.id,
        permiso_id=perm_gestionar.id,
    )
    rp2 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_coord.id,
        permiso_id=perm_ver.id,
    )
    rp3 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_alumno.id,
        permiso_id=perm_reservar.id,
    )
    rp4 = RolePermission(
        tenant_id=tenant.id,
        rol_id=role_alumno.id,
        permiso_id=perm_ver.id,
    )
    db_session.add_all([rp1, rp2, rp3, rp4])
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
        password="Password123!",
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
async def test_evaluacion_creation(db_session: AsyncSession, base_setup: dict):
    evaluacion = Evaluacion(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Primer Coloquio",
    )
    db_session.add(evaluacion)
    await db_session.flush()

    assert evaluacion.id is not None
    assert evaluacion.tipo == TipoEvaluacion.COLOQUIO
    assert evaluacion.estado == EstadoEvaluacion.ABIERTA
    assert "Evaluacion" in repr(evaluacion)


@pytest.mark.asyncio
async def test_turno_evaluacion_creation(db_session: AsyncSession, base_setup: dict):
    evaluacion = Evaluacion(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Test",
    )
    db_session.add(evaluacion)
    await db_session.flush()

    turno = TurnoEvaluacion(
        tenant_id=base_setup["tenant"].id,
        evaluacion_id=evaluacion.id,
        fecha=date(2026, 7, 1),
        hora=time(14, 0),
        max_cupo=2,
    )
    db_session.add(turno)
    await db_session.flush()

    assert turno.id is not None
    assert turno.max_cupo == 2
    assert "TurnoEvaluacion" in repr(turno)


@pytest.mark.asyncio
async def test_convocado_creation(db_session: AsyncSession, base_setup: dict):
    evaluacion = Evaluacion(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Test",
    )
    db_session.add(evaluacion)
    await db_session.flush()

    convocado = Convocado(
        tenant_id=base_setup["tenant"].id,
        evaluacion_id=evaluacion.id,
        alumno_id=base_setup["alumno"].id,
    )
    db_session.add(convocado)
    await db_session.flush()

    assert convocado.id is not None
    assert "Convocado" in repr(convocado)


@pytest.mark.asyncio
async def test_reserva_creation(db_session: AsyncSession, base_setup: dict):
    evaluacion = Evaluacion(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Test",
    )
    db_session.add(evaluacion)
    await db_session.flush()

    turno = TurnoEvaluacion(
        tenant_id=base_setup["tenant"].id,
        evaluacion_id=evaluacion.id,
        fecha=date(2026, 7, 1),
        hora=time(14, 0),
    )
    db_session.add(turno)
    await db_session.flush()

    reserva = ReservaEvaluacion(
        tenant_id=base_setup["tenant"].id,
        turno_id=turno.id,
        alumno_id=base_setup["alumno"].id,
    )
    db_session.add(reserva)
    await db_session.flush()

    assert reserva.id is not None
    assert reserva.estado == EstadoReserva.ACTIVA
    assert "ReservaEvaluacion" in repr(reserva)


@pytest.mark.asyncio
async def test_resultado_creation(db_session: AsyncSession, base_setup: dict):
    evaluacion = Evaluacion(
        tenant_id=base_setup["tenant"].id,
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Test",
    )
    db_session.add(evaluacion)
    await db_session.flush()

    resultado = ResultadoEvaluacion(
        tenant_id=base_setup["tenant"].id,
        evaluacion_id=evaluacion.id,
        alumno_id=base_setup["alumno"].id,
        nota_final="Aprobado",
    )
    db_session.add(resultado)
    await db_session.flush()

    assert resultado.id is not None
    assert resultado.nota_final == "Aprobado"
    assert "ResultadoEvaluacion" in repr(resultado)


@pytest.mark.asyncio
async def test_enum_values():
    assert TipoEvaluacion.COLOQUIO.value == "Coloquio"
    assert TipoEvaluacion.PARCIAL.value == "Parcial"
    assert TipoEvaluacion.TP.value == "TP"
    assert TipoEvaluacion.RECUPERATORIO.value == "Recuperatorio"
    assert EstadoEvaluacion.ABIERTA.value == "Abierta"
    assert EstadoEvaluacion.CERRADA.value == "Cerrada"
    assert EstadoReserva.ACTIVA.value == "Activa"
    assert EstadoReserva.CANCELADA.value == "Cancelada"


# ===================================================================
# 7.2: Tests de convocatoria
# ===================================================================


@pytest.mark.asyncio
async def test_crear_evaluacion_con_turnos(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    service = EvaluacionService(db_session, base_setup["tenant"].id)
    data = EvaluacionCreate(
        materia_id=base_setup["materia"].id,
        cohorte_id=base_setup["cohorte"].id,
        tipo=TipoEvaluacion.COLOQUIO,
        instancia="Primer Coloquio",
        turnos=[
            TurnoEvaluacionCreate(
                fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=2
            ),
            TurnoEvaluacionCreate(
                fecha=date(2026, 7, 2), hora=time(10, 0), max_cupo=1
            ),
        ],
    )
    evaluacion = await service.create(data)
    assert evaluacion.id is not None
    assert evaluacion.instancia == "Primer Coloquio"

    full = await service.get(evaluacion.id)
    assert len(full.turnos) == 2


@pytest.mark.asyncio
async def test_list_evaluaciones(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    service = EvaluacionService(db_session, base_setup["tenant"].id)
    await service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio A",
            turnos=[],
        )
    )
    await service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Coloquio B",
            turnos=[],
        )
    )
    result = await service.list()
    assert len(result) == 2

    filtered = await service.list(materia_id=base_setup["materia"].id)
    assert len(filtered) == 2

    fake_id = UUID("00000000-0000-0000-0000-000000000099")
    filtered_empty = await service.list(materia_id=fake_id)
    assert len(filtered_empty) == 0


@pytest.mark.asyncio
async def test_update_evaluacion(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, EvaluacionUpdate, TurnoEvaluacionCreate

    service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Original",
            turnos=[],
        )
    )
    updated = await service.update(
        evaluacion.id,
        EvaluacionUpdate(instancia="Actualizada", dias_disponibles=10),
    )
    assert updated.instancia == "Actualizada"
    assert updated.dias_disponibles == 10


@pytest.mark.asyncio
async def test_cerrar_evaluacion(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="A cerrar",
            turnos=[],
        )
    )
    cerrada = await service.cerrar(evaluacion.id)
    assert cerrada.estado == EstadoEvaluacion.CERRADA


@pytest.mark.asyncio
async def test_get_evaluacion_404(db_session: AsyncSession, base_setup: dict):
    from fastapi import HTTPException

    service = EvaluacionService(db_session, base_setup["tenant"].id)
    fake_id = UUID("00000000-0000-0000-0000-000000000099")
    with pytest.raises(HTTPException) as exc:
        await service.get(fake_id)
    assert exc.value.status_code == 404


# ===================================================================
# 7.3: Tests de convocados
# ===================================================================


@pytest.mark.asyncio
async def test_importar_convocados(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Convocatoria Test",
            turnos=[],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    count = await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )
    assert count == 2

    convocados = await conv_service.listar(evaluacion.id)
    assert len(convocados) == 2


@pytest.mark.asyncio
async def test_importar_duplicados_ignorados(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Duplicados",
            turnos=[],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    count1 = await conv_service.importar(
        evaluacion.id, [base_setup["alumno"].id]
    )
    assert count1 == 1

    count2 = await conv_service.importar(
        evaluacion.id, [base_setup["alumno"].id, base_setup["alumno2"].id]
    )
    assert count2 == 1

    convocados = await conv_service.listar(evaluacion.id)
    assert len(convocados) == 2


@pytest.mark.asyncio
async def test_remover_convocado(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Remover",
            turnos=[],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    await conv_service.remover(evaluacion.id, base_setup["alumno"].id)
    convocados = await conv_service.listar(evaluacion.id)
    assert len(convocados) == 0


@pytest.mark.asyncio
async def test_remover_con_reserva_activa_409(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="No remover con reserva",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await conv_service.remover(evaluacion.id, base_setup["alumno"].id)
    assert exc.value.status_code == 409


# ===================================================================
# 7.4: Tests de reserva
# ===================================================================


@pytest.mark.asyncio
async def test_reservar_con_cupo(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Reserva Test",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=2
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    reserva = await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )
    assert reserva.estado == EstadoReserva.ACTIVA


@pytest.mark.asyncio
async def test_reservar_sin_cupo_409(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Sin cupo",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=1
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await reserva_service.reservar(
            evaluacion.id, base_setup["alumno2"].id, turno.id
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_reservar_sin_convocado_403(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="No convocado",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await reserva_service.reservar(
            evaluacion.id, base_setup["alumno"].id, turno.id
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_reservar_duplicada_por_alumno_409(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Duplicada",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                ),
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 2), hora=time(10, 0), max_cupo=5
                ),
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await eval_service.get(evaluacion.id)
    turno1 = full.turnos[0]
    turno2 = full.turnos[1]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno1.id
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await reserva_service.reservar(
            evaluacion.id, base_setup["alumno"].id, turno2.id
        )
    assert exc.value.status_code == 409


# ===================================================================
# 7.5: Tests de cancelación
# ===================================================================


@pytest.mark.asyncio
async def test_cancelar_propia_reserva(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Cancelar propia",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    reserva = await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    await reserva_service.cancelar(reserva.id, base_setup["alumno"].id)

    reservas = await reserva_service.listar_por_evaluacion(evaluacion.id)
    activas = [r for r in reservas if r.estado == EstadoReserva.ACTIVA]
    assert len(activas) == 0


@pytest.mark.asyncio
async def test_cancelar_reserva_ajena_403(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Cancelar ajena",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    reserva = await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await reserva_service.cancelar(reserva.id, base_setup["alumno2"].id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_cancelar_ya_cancelada_400(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Ya cancelada",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    reserva = await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    await reserva_service.cancelar(reserva.id, base_setup["alumno"].id)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await reserva_service.cancelar(reserva.id, base_setup["alumno"].id)
    assert exc.value.status_code == 400


# ===================================================================
# 7.6: Tests de resultados
# ===================================================================


@pytest.mark.asyncio
async def test_registrar_resultado(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Resultados",
            turnos=[],
        )
    )

    resultado_service = ResultadoService(db_session, base_setup["tenant"].id)
    resultado = await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno"].id, "Aprobado"
    )
    assert resultado.nota_final == "Aprobado"
    assert resultado.alumno_id == base_setup["alumno"].id


@pytest.mark.asyncio
async def test_actualizar_resultado(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Actualizar nota",
            turnos=[],
        )
    )

    resultado_service = ResultadoService(db_session, base_setup["tenant"].id)
    await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno"].id, "Regular"
    )
    updated = await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno"].id, "Promocionado"
    )
    assert updated.nota_final == "Promocionado"


@pytest.mark.asyncio
async def test_listar_resultados(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Listar",
            turnos=[],
        )
    )

    resultado_service = ResultadoService(db_session, base_setup["tenant"].id)
    await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno"].id, "Aprobado"
    )
    await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno2"].id, "Regular"
    )

    resultados = await resultado_service.listar(evaluacion.id)
    assert len(resultados) == 2


@pytest.mark.asyncio
async def test_export_csv(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="CSV Export",
            turnos=[],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )

    resultado_service = ResultadoService(db_session, base_setup["tenant"].id)
    await resultado_service.registrar_o_actualizar(
        evaluacion.id, base_setup["alumno"].id, "Aprobado"
    )

    csv_content = await resultado_service.export_csv(evaluacion.id)
    assert "alummo_id,nota_final" in csv_content
    assert "Aprobado" in csv_content


# ===================================================================
# 7.7: Tests de métricas
# ===================================================================


@pytest.mark.asyncio
async def test_metricas_globales(db_session: AsyncSession, base_setup: dict):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Metricas Globales",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=2
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )

    metricas = MetricasService(db_session, base_setup["tenant"].id)
    result = await metricas.globales()

    assert result["total_convocatorias"] >= 1
    assert result["total_convocados"] >= 2


@pytest.mark.asyncio
async def test_metricas_por_convocatoria(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    eval_service = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await eval_service.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Metricas Conv",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=3
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(
        evaluacion.id,
        [base_setup["alumno"].id, base_setup["alumno2"].id],
    )

    full = await eval_service.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service = ReservaService(db_session, base_setup["tenant"].id)
    await reserva_service.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    metricas = MetricasService(db_session, base_setup["tenant"].id)
    result = await metricas.por_convocatoria(evaluacion.id)

    assert result["convocados"] == 2
    assert result["reservas_activas"] == 1
    assert result["cupos_libres"] == 2
    assert result["resultados_registrados"] == 0


# ===================================================================
# 7.8: Tests de permisos
# ===================================================================


@pytest.mark.asyncio
async def test_coloquios_sin_permiso_403(
    client: TestClient, db_session: AsyncSession
):
    clear_all_caches()
    await _setup_base(db_session)
    headers = await _auth_header(client, email=_SIN_PERM_EMAIL)

    response = client.get("/api/v1/coloquios", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_crear_sin_gestionar_permiso_403(
    client: TestClient, db_session: AsyncSession
):
    clear_all_caches()
    await _setup_base(db_session)
    headers = await _auth_header(client, email=_ALUMNO_EMAIL)

    payload = {
        "materia_id": "00000000-0000-0000-0000-000000000001",
        "cohorte_id": "00000000-0000-0000-0000-000000000001",
        "tipo": "Coloquio",
        "instancia": "Test",
        "turnos": [],
    }
    response = client.post(
        "/api/v1/coloquios",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 403


# ===================================================================
# 7.9: Tests de aislamiento multi-tenant
# ===================================================================


@pytest.mark.asyncio
async def test_evaluaciones_aisladas_por_tenant(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    service_a = EvaluacionService(db_session, base_setup["tenant"].id)
    await service_a.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Solo tenant A",
            turnos=[],
        )
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-b", name="Tenant B")
    service_b = EvaluacionService(db_session, tenant_b.id)
    evals_b = await service_b.list()
    assert len(evals_b) == 0


@pytest.mark.asyncio
async def test_reservas_aisladas_por_tenant(
    db_session: AsyncSession, base_setup: dict
):
    from app.schemas.evaluaciones import EvaluacionCreate, TurnoEvaluacionCreate

    service_a = EvaluacionService(db_session, base_setup["tenant"].id)
    evaluacion = await service_a.create(
        EvaluacionCreate(
            materia_id=base_setup["materia"].id,
            cohorte_id=base_setup["cohorte"].id,
            tipo=TipoEvaluacion.COLOQUIO,
            instancia="Aislar reservas",
            turnos=[
                TurnoEvaluacionCreate(
                    fecha=date(2026, 7, 1), hora=time(14, 0), max_cupo=5
                )
            ],
        )
    )

    conv_service = ConvocadoService(db_session, base_setup["tenant"].id)
    await conv_service.importar(evaluacion.id, [base_setup["alumno"].id])

    full = await service_a.get(evaluacion.id)
    turno = full.turnos[0]

    reserva_service_a = ReservaService(db_session, base_setup["tenant"].id)
    await reserva_service_a.reservar(
        evaluacion.id, base_setup["alumno"].id, turno.id
    )

    tenant_b = await create_test_tenant(db_session, slug="tenant-c", name="Tenant C")
    reserva_service_b = ReservaService(db_session, tenant_b.id)
    reservas_b = await reserva_service_b.listar_mis_reservas(
        base_setup["alumno"].id
    )
    assert len(reservas_b) == 0
