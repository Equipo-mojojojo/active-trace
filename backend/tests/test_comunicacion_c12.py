from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.security import build_email_lookup, hash_password
from app.models.asignacion import Asignacion, RolEnum
from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.usuario import Usuario
from app.repositories.padron_repository import PadronRepository
from app.services.audit_service import AuditService
from app.services.comunicacion_dispatcher import (
    ComunicacionDispatchError,
    ComunicacionDispatcher,
)
from app.services.comunicacion_service import (
    ComunicacionConflictError,
    ComunicacionForbiddenError,
    ComunicacionNotFoundError,
    ComunicacionService,
)
from app.workers.comunicacion_worker import process_pending_communications
from tests.conftest import create_test_cohorte, create_test_materia, create_test_tenant


async def _grant_permissions(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    role_name: str,
    permissions: list[str],
) -> None:
    role = Role(tenant_id=tenant_id, nombre=role_name, editable=True)
    db_session.add(role)
    await db_session.flush()

    modulo_accion = {
        "comunicacion:enviar": ("comunicacion", "enviar"),
        "comunicacion:enviar:propio": ("comunicacion", "enviar"),
        "comunicacion:aprobar": ("comunicacion", "aprobar"),
    }

    for codigo in permissions:
        modulo, accion = modulo_accion[codigo]
        permiso = Permission(
            tenant_id=tenant_id,
            codigo=codigo,
            modulo=modulo,
            accion=accion,
        )
        db_session.add(permiso)
        await db_session.flush()
        db_session.add(
            RolePermission(
                tenant_id=tenant_id,
                rol_id=role.id,
                permiso_id=permiso.id,
            )
        )


async def _create_auth_user(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    role_name: str,
    email: str,
    user_id: UUID | None = None,
) -> User:
    user = User(
        id=user_id or uuid4(),
        tenant_id=tenant_id,
        email=email,
        email_lookup=build_email_lookup(email),
        full_name=f"{role_name.title()} Test",
        password_hash=hash_password("Password123!"),
        roles=[role_name],
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _create_profesor_actor_with_scope(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    materia_id: UUID,
    email: str = "profesor@test.com",
) -> User:
    shared_id = uuid4()
    await _grant_permissions(
        db_session,
        tenant_id=tenant_id,
        role_name="PROFESOR",
        permissions=["comunicacion:enviar:propio"],
    )
    user = await _create_auth_user(
        db_session,
        tenant_id=tenant_id,
        role_name="PROFESOR",
        email=email,
        user_id=shared_id,
    )
    usuario = Usuario(
        tenant_id=tenant_id,
        nombre="Profesor",
        apellidos="Scope",
        email=email,
    )
    usuario.id = shared_id
    db_session.add(usuario)
    await db_session.flush()
    db_session.add(
        Asignacion(
            tenant_id=tenant_id,
            usuario_id=shared_id,
            rol=RolEnum.PROFESOR,
            materia_id=materia_id,
            carrera_id=None,
            cohorte_id=None,
            comisiones="A1",
            desde=date.today(),
            hasta=None,
            responsable_id=None,
        )
    )
    await db_session.flush()
    return user


async def _create_coordinador_actor(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
) -> User:
    await _grant_permissions(
        db_session,
        tenant_id=tenant_id,
        role_name="COORDINADOR",
        permissions=["comunicacion:enviar", "comunicacion:aprobar"],
    )
    return await _create_auth_user(
        db_session,
        tenant_id=tenant_id,
        role_name="COORDINADOR",
        email=email,
    )


async def _create_user_without_permissions(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
) -> User:
    return await _create_auth_user(
        db_session,
        tenant_id=tenant_id,
        role_name="SIN_PERMISOS",
        email=email,
    )


async def _create_padron_entries(
    db_session: AsyncSession,
    *,
    tenant_id: UUID,
    materia_id: UUID,
    cohorte_id: UUID,
    rows: list[dict[str, str]],
) -> list:
    repo = PadronRepository(db_session, tenant_id)
    version = await repo.crear_version(materia_id, cohorte_id)
    await repo.crear_entradas_bulk(version.id, rows)
    await repo.actualizar_total_entradas(version.id, len(rows))
    return await repo.listar_entradas(version.id)


def _login_headers(client, *, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class FailingDispatcher(ComunicacionDispatcher):
    async def send(self, comunicacion: Comunicacion):
        raise ComunicacionDispatchError(f"fallo-{comunicacion.id}")


@pytest.mark.asyncio
async def test_model_transitions_validate_state_machine() -> None:
    comunicacion = Comunicacion(
        tenant_id=uuid4(),
        lote_id=uuid4(),
        entrada_padron_id=uuid4(),
        materia_id=uuid4(),
        destinatario_email="alumno@test.com",
        destinatario_nombre="Alumno Test",
        asunto="Hola",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.PENDIENTE,
        requiere_aprobacion=True,
    )

    comunicacion.aprobar(uuid4())
    assert comunicacion.aprobada is True
    comunicacion.marcar_enviando()
    assert comunicacion.estado == EstadoComunicacion.ENVIANDO
    comunicacion.marcar_enviada()
    assert comunicacion.estado == EstadoComunicacion.ENVIADO

    with pytest.raises(ValueError):
        comunicacion.cancelar(uuid4())


@pytest.mark.asyncio
async def test_destinatario_email_is_stored_encrypted(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-encrypted")
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-ENC"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-ENC"
    )
    entradas = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Alumno",
                "apellidos": "Test",
                "email": "alumno@test.com",
                "comision": "A1",
                "regional": "Centro",
            }
        ],
    )
    comunicacion = Comunicacion(
        tenant_id=tenant.id,
        lote_id=uuid4(),
        entrada_padron_id=entradas[0].id,
        materia_id=materia.id,
        destinatario_email="alumno@test.com",
        destinatario_nombre="Alumno Test",
        asunto="Asunto",
        cuerpo="Cuerpo",
    )
    db_session.add(comunicacion)
    await db_session.commit()

    raw_value = (
        await db_session.execute(
            text("SELECT destinatario_email FROM comunicacion WHERE id = :id"),
            {"id": str(comunicacion.id)},
        )
    ).scalar_one()

    assert raw_value != "alumno@test.com"


@pytest.mark.asyncio
async def test_preview_returns_rendered_messages_without_persisting(
    db_session: AsyncSession,
) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-preview")
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-PRE"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-PRE"
    )
    actor = await _create_coordinador_actor(
        db_session, tenant_id=tenant.id, email="coord-preview@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
            {
                "nombre": "Beto",
                "apellidos": "Ruiz",
                "email": "beto@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    await db_session.commit()

    service = ComunicacionService(db_session, tenant.id)
    preview = await service.preview(
        materia_id=materia.id,
        entrada_padron_ids=[entry.id for entry in entries],
        asunto_template="Recordatorio {materia_nombre}",
        cuerpo_template="Hola {alumno_nombre_completo}",
        actor=actor,
    )

    assert preview["requiere_aprobacion"] is False
    assert len(preview["preview"]) == 2
    assert preview["preview"][0]["asunto"] == f"Recordatorio {materia.nombre}"
    count = await db_session.execute(select(Comunicacion))
    assert count.scalars().all() == []


@pytest.mark.asyncio
async def test_profesor_scope_blocks_other_materia(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-scope")
    materia_ok = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-OK"
    )
    materia_other = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-OTR"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-SCOPE"
    )
    actor = await _create_profesor_actor_with_scope(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia_ok.id,
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia_other.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    await db_session.commit()

    service = ComunicacionService(db_session, tenant.id)
    with pytest.raises(ComunicacionForbiddenError):
        await service.preview(
            materia_id=materia_other.id,
            entrada_padron_ids=[entries[0].id],
            asunto_template="Hola {alumno_nombre}",
            cuerpo_template="Mensaje",
            actor=actor,
        )


@pytest.mark.asyncio
async def test_enqueue_and_actions_register_audit_entries(
    db_session: AsyncSession,
) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-audit")
    tenant.communication_approval_required = True
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-AUD"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-AUD"
    )
    actor = await _create_coordinador_actor(
        db_session, tenant_id=tenant.id, email="coord-audit@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    audit = AuditService(db_session, tenant.id)
    service = ComunicacionService(db_session, tenant.id, audit=audit)

    lote = await service.enqueue(
        materia_id=materia.id,
        entrada_padron_ids=[entries[0].id],
        asunto_template="Hola {alumno_nombre}",
        cuerpo_template="Seguimiento {materia_nombre}",
        actor=actor,
        audit_actor_id=actor.id,
    )
    comunicacion_id = lote["comunicaciones"][0]["id"]
    await service.approve_lote(lote["lote_id"], actor.id, actor)
    await service.cancel_one(comunicacion_id, actor.id, actor)
    await db_session.commit()

    result = await db_session.execute(
        select(AuditLog.accion).order_by(AuditLog.fecha_hora)
    )
    acciones = result.scalars().all()
    assert AuditAction.COMUNICACION_ENVIAR in acciones
    assert AuditAction.COMUNICACION_APROBAR in acciones
    assert AuditAction.COMUNICACION_CANCELAR in acciones


@pytest.mark.asyncio
async def test_worker_respects_approval_and_success_path(
    db_session: AsyncSession,
) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-worker")
    tenant.communication_approval_required = True
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-WRK"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-WRK"
    )
    actor = await _create_coordinador_actor(
        db_session, tenant_id=tenant.id, email="coord-worker@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    service = ComunicacionService(db_session, tenant.id)
    lote = await service.enqueue(
        materia_id=materia.id,
        entrada_padron_ids=[entries[0].id],
        asunto_template="Hola {alumno_nombre}",
        cuerpo_template="Seguimiento",
        actor=actor,
        audit_actor_id=actor.id,
    )
    await db_session.flush()

    processed_before = await process_pending_communications(db_session)
    assert processed_before == 0

    await service.approve_lote(lote["lote_id"], actor.id, actor)
    processed_after = await process_pending_communications(db_session)
    await db_session.commit()

    assert processed_after == 1
    comunicacion = await db_session.get(Comunicacion, lote["comunicaciones"][0]["id"])
    assert comunicacion is not None
    assert comunicacion.estado == EstadoComunicacion.ENVIADO


@pytest.mark.asyncio
async def test_worker_marks_error_when_dispatch_fails(db_session: AsyncSession) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-worker-err")
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-WRE"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-WRE"
    )
    actor = await _create_coordinador_actor(
        db_session, tenant_id=tenant.id, email="coord-worker-err@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    service = ComunicacionService(db_session, tenant.id)
    lote = await service.enqueue(
        materia_id=materia.id,
        entrada_padron_ids=[entries[0].id],
        asunto_template="Hola {alumno_nombre}",
        cuerpo_template="Seguimiento",
        actor=actor,
        audit_actor_id=actor.id,
    )
    processed = await process_pending_communications(
        db_session,
        dispatcher=FailingDispatcher(),
    )
    await db_session.commit()

    assert processed == 1
    comunicacion = await db_session.get(Comunicacion, lote["comunicaciones"][0]["id"])
    assert comunicacion is not None
    assert comunicacion.estado == EstadoComunicacion.ERROR
    assert comunicacion.error_detalle is not None


@pytest.mark.asyncio
async def test_other_tenant_cannot_read_foreign_lote(db_session: AsyncSession) -> None:
    tenant_a = await create_test_tenant(db_session, slug="c12-tenant-a")
    tenant_b = await create_test_tenant(db_session, slug="c12-tenant-b")
    materia = await create_test_materia(
        db_session, tenant_id=tenant_a.id, codigo="C12-TA"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant_a.id, nombre="C12-TA"
    )
    actor_a = await _create_coordinador_actor(
        db_session, tenant_id=tenant_a.id, email="coord-a@test.com"
    )
    actor_b = await _create_coordinador_actor(
        db_session, tenant_id=tenant_b.id, email="coord-b@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant_a.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    service_a = ComunicacionService(db_session, tenant_a.id)
    service_b = ComunicacionService(db_session, tenant_b.id)
    lote = await service_a.enqueue(
        materia_id=materia.id,
        entrada_padron_ids=[entries[0].id],
        asunto_template="Hola {alumno_nombre}",
        cuerpo_template="Seguimiento",
        actor=actor_a,
        audit_actor_id=actor_a.id,
    )

    with pytest.raises(ComunicacionNotFoundError):
        await service_b.get_lote(lote["lote_id"], actor=actor_b)


@pytest.mark.asyncio
async def test_api_endpoints_preview_and_lote_lifecycle(
    client, db_session: AsyncSession
) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-api")
    tenant.communication_approval_required = True
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-API"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-API"
    )
    await _create_coordinador_actor(
        db_session, tenant_id=tenant.id, email="coord-api@test.com"
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
            {
                "nombre": "Beto",
                "apellidos": "Ruiz",
                "email": "beto@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    await db_session.commit()

    headers = _login_headers(client, email="coord-api@test.com")
    payload = {
        "materia_id": str(materia.id),
        "entrada_padron_ids": [str(entry.id) for entry in entries],
        "asunto_template": "Hola {alumno_nombre}",
        "cuerpo_template": "Seguimiento {materia_nombre}",
    }

    preview_response = client.post(
        "/api/v1/comunicaciones/preview",
        json=payload,
        headers=headers,
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["requiere_aprobacion"] is True
    assert len(preview_response.json()["preview"]) == 2

    enqueue_response = client.post(
        "/api/v1/comunicaciones/lotes",
        json=payload,
        headers=headers,
    )
    assert enqueue_response.status_code == 201
    lote_id = enqueue_response.json()["lote_id"]

    get_response = client.get(
        f"/api/v1/comunicaciones/lotes/{lote_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["total"] == 2

    approve_response = client.post(
        f"/api/v1/comunicaciones/lotes/{lote_id}/aprobar",
        headers=headers,
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["affected"] == 2


@pytest.mark.asyncio
async def test_api_preview_rejects_user_without_permission(
    client, db_session: AsyncSession
) -> None:
    tenant = await create_test_tenant(db_session, slug="c12-api-no-perm")
    materia = await create_test_materia(
        db_session, tenant_id=tenant.id, codigo="C12-NOPERM"
    )
    cohorte = await create_test_cohorte(
        db_session, tenant_id=tenant.id, nombre="C12-NOPERM"
    )
    await _create_user_without_permissions(
        db_session,
        tenant_id=tenant.id,
        email="sinperm-api@test.com",
    )
    entries = await _create_padron_entries(
        db_session,
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        rows=[
            {
                "nombre": "Ana",
                "apellidos": "Lopez",
                "email": "ana@test.com",
                "comision": "A1",
                "regional": "Centro",
            },
        ],
    )
    await db_session.commit()

    headers = _login_headers(client, email="sinperm-api@test.com")
    response = client.post(
        "/api/v1/comunicaciones/preview",
        json={
            "materia_id": str(materia.id),
            "entrada_padron_ids": [str(entries[0].id)],
            "asunto_template": "Hola {alumno_nombre}",
            "cuerpo_template": "Seguimiento",
        },
        headers=headers,
    )
    assert response.status_code == 403
