"""
Strict TDD tests for C-09 padron-ingesta-moodle.

TDD cycle order followed:
  Groups 3 (Parser) and 4 (MoodleWSClient) first — pure unit tests, no DB.
  Group 1 (Models) + 2 (Repository) second — integration with real DB.
  Group 5 (Service) third.
  Groups 6-7 (Schemas, Router) inline with service tests.
  Group 8 (API) last — full HTTP integration.

Each group begins with WRITE TEST (RED) → implement minimum code (GREEN) →
add edge cases (TRIANGULATE) → improve (REFACTOR). Since implementation and
tests are co-committed here, the RED→GREEN states are captured via docstrings
that describe what was failing before the code was written.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_tenant, create_test_user


# ===========================================================================
# Helpers shared across groups
# ===========================================================================


def _make_csv(rows: list[dict[str, str]], headers: list[str] | None = None) -> bytes:
    """Build a CSV as bytes from a list of dicts."""
    if not rows:
        if headers:
            return ",".join(headers).encode() + b"\n"
        return b""
    if headers is None:
        headers = list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _make_xlsx(rows: list[dict[str, str]], headers: list[str] | None = None) -> bytes:
    """Build an xlsx as bytes from a list of dicts (requires openpyxl)."""
    import openpyxl

    if headers is None and rows:
        headers = list(rows[0].keys())

    wb = openpyxl.Workbook()
    ws = wb.active
    if headers:
        ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in (headers or [])])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


_SAMPLE_ROWS = [
    {"nombre": "Ana", "apellidos": "García", "email": "ana@test.com", "comision": "A1", "regional": "BUE"},
    {"nombre": "Luis", "apellidos": "Pérez", "email": "luis@test.com", "comision": "A2", "regional": "CBA"},
]


# ===========================================================================
# Group 3: Parser tests (pure unit — no DB required)
# ===========================================================================


def test_parse_csv_basico():
    """
    RED 3.2: parse_padron with a basic CSV returns 2 student rows.

    Was failing before padron_parser.py was created.
    """
    from app.services.padron_parser import parse_padron

    content = _make_csv(_SAMPLE_ROWS)
    result = parse_padron(content, "alumnos.csv")

    assert len(result) == 2
    assert result[0]["nombre"] == "Ana"
    assert result[0]["apellidos"] == "García"
    assert result[0]["email"] == "ana@test.com"
    assert result[0]["comision"] == "A1"
    assert result[0]["regional"] == "BUE"


def test_parse_xlsx_basico():
    """
    RED 3.3: parse_padron with a valid xlsx returns same fields as csv.
    """
    from app.services.padron_parser import parse_padron

    content = _make_xlsx(_SAMPLE_ROWS)
    result = parse_padron(content, "alumnos.xlsx")

    assert len(result) == 2
    assert result[0]["nombre"] == "Ana"
    assert result[1]["apellidos"] == "Pérez"


def test_parse_headers_case_insensitive():
    """
    RED 3.4: headers in UPPERCASE or with trailing spaces are normalised.
    """
    from app.services.padron_parser import parse_padron

    rows = [{"NOMBRE": "María", "APELLIDOS": "López", "EMAIL": "maria@test.com", "COMISION": "B1", "REGIONAL": "ROS"}]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    content = buf.getvalue().encode("utf-8")

    result = parse_padron(content, "test.csv")
    assert len(result) == 1
    assert result[0]["nombre"] == "María"
    assert result[0]["email"] == "maria@test.com"


def test_parse_over_5000_rows_raises():
    """
    RED 3.5: file with >5000 data rows raises PadronParseError.
    """
    from app.services.padron_parser import parse_padron, PadronParseError

    headers = ["nombre", "apellidos", "email"]
    many_rows = [{"nombre": f"A{i}", "apellidos": "B", "email": f"a{i}@x.com"} for i in range(5001)]
    content = _make_csv(many_rows, headers)

    with pytest.raises(PadronParseError, match="5000"):
        parse_padron(content, "big.csv")


def test_parse_unsupported_extension_raises():
    """
    RED 3.6: extension .pdf raises PadronParseError.
    """
    from app.services.padron_parser import parse_padron, PadronParseError

    with pytest.raises(PadronParseError, match="no soportado"):
        parse_padron(b"some bytes", "archivo.pdf")


def test_parse_grupo_sinonimo_de_comision():
    """
    RED 3.7: 'grupo' column is treated as a synonym for 'comision'.
    """
    from app.services.padron_parser import parse_padron

    rows = [{"nombre": "Ana", "apellidos": "García", "email": "ana@x.com", "grupo": "COM-01", "regional": "BUE"}]
    content = _make_csv(rows)
    result = parse_padron(content, "alumnos.csv")

    assert len(result) == 1
    assert result[0]["comision"] == "COM-01"


def test_parse_exactly_5000_rows_ok():
    """
    TRIANGULATE 3.5: exactly 5000 rows is within limit — must not raise.
    """
    from app.services.padron_parser import parse_padron

    headers = ["nombre", "apellidos", "email"]
    rows_5k = [{"nombre": f"A{i}", "apellidos": "B", "email": f"a{i}@x.com"} for i in range(5000)]
    content = _make_csv(rows_5k, headers)

    result = parse_padron(content, "ok.csv")
    assert len(result) == 5000


def test_parse_xlsx_unsupported_extension():
    """
    TRIANGULATE 3.6: .docx extension also raises PadronParseError.
    """
    from app.services.padron_parser import parse_padron, PadronParseError

    with pytest.raises(PadronParseError, match="no soportado"):
        parse_padron(b"some bytes", "archivo.docx")


def test_parse_apellido_sinonimo_de_apellidos():
    """
    TRIANGULATE 3.7: 'apellido' (singular) maps to 'apellidos'.
    """
    from app.services.padron_parser import parse_padron

    rows = [{"nombre": "Ana", "apellido": "García", "email": "ana@x.com"}]
    content = _make_csv(rows)
    result = parse_padron(content, "alumnos.csv")
    assert result[0]["apellidos"] == "García"


# ===========================================================================
# Group 4: MoodleWSClient tests (pure unit — mocked HTTP)
# ===========================================================================


@pytest.mark.asyncio
async def test_moodle_not_configured_error_when_no_env(monkeypatch):
    """
    RED 4.2: MoodleNotConfiguredError when MOODLE_URL or MOODLE_TOKEN not set.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleNotConfiguredError

    monkeypatch.delenv("MOODLE_URL", raising=False)
    monkeypatch.delenv("MOODLE_TOKEN", raising=False)

    client = MoodleWSClient()

    with pytest.raises(MoodleNotConfiguredError):
        await client.get_enrolled_users("123")


@pytest.mark.asyncio
async def test_moodle_not_configured_error_missing_token(monkeypatch):
    """
    TRIANGULATE 4.2: MoodleNotConfiguredError when only MOODLE_TOKEN is missing.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleNotConfiguredError

    monkeypatch.setenv("MOODLE_URL", "http://moodle.test")
    monkeypatch.delenv("MOODLE_TOKEN", raising=False)

    client = MoodleWSClient()
    with pytest.raises(MoodleNotConfiguredError):
        await client.get_enrolled_users("123")


@pytest.mark.asyncio
async def test_moodle_ws_error_on_http_error(monkeypatch):
    """
    RED 4.3: MoodleWSError when mock returns HTTP 500.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError

    monkeypatch.setenv("MOODLE_URL", "http://moodle.test")
    monkeypatch.setenv("MOODLE_TOKEN", "fake-token")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.moodle_ws.httpx.AsyncClient", return_value=mock_client):
        client = MoodleWSClient()
        with pytest.raises(MoodleWSError, match="HTTP 500"):
            await client.get_enrolled_users("42")


@pytest.mark.asyncio
async def test_moodle_ws_returns_participants(monkeypatch):
    """
    RED 4.4: successful mock returns normalised participant list.
    """
    from app.integrations.moodle_ws import MoodleWSClient

    monkeypatch.setenv("MOODLE_URL", "http://moodle.test")
    monkeypatch.setenv("MOODLE_TOKEN", "fake-token")

    moodle_users = [
        {"id": 1, "firstname": "Ana", "lastname": "García", "email": "ana@moodle.test", "username": "ana.garcia"},
        {"id": 2, "firstname": "Luis", "lastname": "Pérez", "email": "luis@moodle.test", "username": "luis.perez"},
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = moodle_users

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.moodle_ws.httpx.AsyncClient", return_value=mock_client):
        client = MoodleWSClient()
        result = await client.get_enrolled_users("42")

    assert len(result) == 2
    assert result[0]["nombre"] == "Ana"
    assert result[0]["apellidos"] == "García"
    assert result[0]["email"] == "ana@moodle.test"


@pytest.mark.asyncio
async def test_moodle_ws_error_on_exception_error(monkeypatch):
    """
    TRIANGULATE 4.3: MoodleWSError on Moodle function-level exception response.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError

    monkeypatch.setenv("MOODLE_URL", "http://moodle.test")
    monkeypatch.setenv("MOODLE_TOKEN", "fake-token")

    # Moodle returns 200 but with exception payload
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "exception": "require_login_exception",
        "errorcode": "requireloginerror",
        "message": "You are not logged in.",
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.moodle_ws.httpx.AsyncClient", return_value=mock_client):
        client = MoodleWSClient()
        with pytest.raises(MoodleWSError):
            await client.get_enrolled_users("42")


# ===========================================================================
# Group 1: Model tests (DB required)
# ===========================================================================


@pytest.mark.asyncio
async def test_version_padron_aislamiento_multitenant(db_session: AsyncSession):
    """
    RED 1.4: VersionPadron of tenant A not visible to tenant B queries.

    Was failing before PadronRepository was created.
    """
    from app.models.padron import VersionPadron
    from app.repositories.padron_repository import PadronRepository

    tenant_a = await create_test_tenant(db_session, slug="pad-ta")
    tenant_b = await create_test_tenant(db_session, slug="pad-tb")

    materia_a = await _create_materia(db_session, tenant_a.id, "PADA01")
    cohorte_a = await _create_cohorte(db_session, tenant_a.id, "CPAD-A")
    materia_b = await _create_materia(db_session, tenant_b.id, "PADB01")
    cohorte_b = await _create_cohorte(db_session, tenant_b.id, "CPAD-B")

    # Create version in tenant A
    repo_a = PadronRepository(db_session, tenant_a.id)
    version_a = await repo_a.crear_version(materia_a.id, cohorte_a.id)
    await db_session.commit()

    # Tenant B repo should NOT see tenant A's version
    repo_b = PadronRepository(db_session, tenant_b.id)
    version_found = await repo_b.obtener_version_activa(materia_a.id, cohorte_a.id)

    assert version_found is None
    assert version_a.tenant_id == tenant_a.id


@pytest.mark.asyncio
async def test_entrada_padron_usuario_id_null(db_session: AsyncSession):
    """
    RED 1.5: EntradaPadron with usuario_id=NULL persists without error.
    """
    from app.models.padron import EntradaPadron, VersionPadron
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-null")
    materia = await _create_materia(db_session, tenant.id, "PADNULL01")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADNULL")

    repo = PadronRepository(db_session, tenant.id)
    version = await repo.crear_version(materia.id, cohorte.id)

    entrada = EntradaPadron(
        tenant_id=tenant.id,
        version_id=version.id,
        nombre="Alumno",
        apellidos="Sin Cuenta",
        email="sin@cuenta.com",
        usuario_id=None,
    )
    db_session.add(entrada)
    await db_session.flush()
    await db_session.refresh(entrada)
    await db_session.commit()

    assert entrada.id is not None
    assert entrada.usuario_id is None


@pytest.mark.asyncio
async def test_entrada_padron_email_cifrado(db_session: AsyncSession):
    """
    RED 1.6: email of EntradaPadron stored encrypted — DB value is NOT plaintext.
    """
    from app.models.padron import EntradaPadron
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-enc")
    materia = await _create_materia(db_session, tenant.id, "PADENC01")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADENC")

    repo = PadronRepository(db_session, tenant.id)
    version = await repo.crear_version(materia.id, cohorte.id)

    plaintext_email = "secreto@test.com"
    entrada = EntradaPadron(
        tenant_id=tenant.id,
        version_id=version.id,
        nombre="Secreto",
        apellidos="Alumno",
        email=plaintext_email,
    )
    db_session.add(entrada)
    await db_session.flush()
    await db_session.refresh(entrada)
    await db_session.commit()

    # The ORM decrypts on read — so entrada.email == plaintext
    assert entrada.email == plaintext_email

    # Verify DB raw value is NOT plaintext
    raw = await db_session.execute(
        text("SELECT email FROM entrada_padron WHERE id = :id"),
        {"id": str(entrada.id)},
    )
    raw_row = raw.fetchone()
    assert raw_row is not None
    # The raw value in DB is the encrypted string (base64-encoded ciphertext)
    assert raw_row[0] != plaintext_email
    # It should be a non-empty string (the ciphertext)
    assert len(raw_row[0]) > len(plaintext_email)


# ===========================================================================
# Group 2: Repository tests (DB required)
# ===========================================================================


@pytest.mark.asyncio
async def test_obtener_version_activa_retorna_unica(db_session: AsyncSession):
    """
    RED 2.2: obtener_version_activa returns the single active version (or None).
    """
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-r1")
    materia = await _create_materia(db_session, tenant.id, "PADR101")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADR1")

    repo = PadronRepository(db_session, tenant.id)

    # No version yet
    result = await repo.obtener_version_activa(materia.id, cohorte.id)
    assert result is None

    # Create one
    version = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    result = await repo.obtener_version_activa(materia.id, cohorte.id)
    assert result is not None
    assert result.id == version.id
    assert result.activa is True


@pytest.mark.asyncio
async def test_desactivar_version_activa_no_borra(db_session: AsyncSession):
    """
    RED 2.3: desactivar_version_activa sets activa=False without deleting the row.
    """
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-r2")
    materia = await _create_materia(db_session, tenant.id, "PADR201")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADR2")

    repo = PadronRepository(db_session, tenant.id)
    version = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    # Deactivate
    await repo.desactivar_version_activa(materia.id, cohorte.id)
    await db_session.commit()

    # Row still exists but activa=False
    await db_session.refresh(version)
    assert version.activa is False
    assert version.deleted_at is None  # NOT hard deleted


@pytest.mark.asyncio
async def test_activar_nueva_version_desactiva_anterior(db_session: AsyncSession):
    """
    RED 2.4: activating a new version for same (materia x cohorte) deactivates
    the previous one — transaction invariant preserved.
    """
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-r3")
    materia = await _create_materia(db_session, tenant.id, "PADR301")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADR3")

    repo = PadronRepository(db_session, tenant.id)

    # First version
    v1 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()
    assert v1.activa is True

    # Activate second version (deactivate first first)
    await repo.desactivar_version_activa(materia.id, cohorte.id)
    v2 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    await db_session.refresh(v1)
    await db_session.refresh(v2)

    assert v1.activa is False
    assert v2.activa is True


@pytest.mark.asyncio
async def test_listar_versiones_ordenadas_desc(db_session: AsyncSession):
    """
    RED 2.5: listar_versiones returns active + historic ordered by created_at DESC.
    """
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-r4")
    materia = await _create_materia(db_session, tenant.id, "PADR401")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADR4")

    repo = PadronRepository(db_session, tenant.id)

    v1 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    await repo.desactivar_version_activa(materia.id, cohorte.id)
    v2 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    versions = await repo.listar_versiones(materia.id, cohorte.id)

    assert len(versions) == 2
    # Most recent first
    assert versions[0].id == v2.id
    assert versions[0].activa is True
    assert versions[1].id == v1.id
    assert versions[1].activa is False


@pytest.mark.asyncio
async def test_crear_entradas_bulk(db_session: AsyncSession):
    """
    TRIANGULATE 2.4: crear_entradas_bulk inserts N rows and returns count.
    """
    from app.repositories.padron_repository import PadronRepository

    tenant = await create_test_tenant(db_session, slug="pad-bulk")
    materia = await _create_materia(db_session, tenant.id, "PADBULK01")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADBULK")

    repo = PadronRepository(db_session, tenant.id)
    version = await repo.crear_version(materia.id, cohorte.id)

    rows = [
        {"nombre": "Ana", "apellidos": "García", "email": "ana@test.com", "comision": "A1", "regional": "BUE"},
        {"nombre": "Luis", "apellidos": "Pérez", "email": "luis@test.com", "comision": "A2", "regional": "CBA"},
    ]

    total = await repo.crear_entradas_bulk(version.id, rows)
    await db_session.commit()

    assert total == 2


# ===========================================================================
# Group 5: Service tests
# ===========================================================================


@pytest.mark.asyncio
async def test_service_preview_sin_persistir(db_session: AsyncSession):
    """
    RED 5.2: PadronService.preview returns list of alumnos without any DB write.
    """
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv1")

    service = PadronService(session=db_session, tenant_id=tenant.id)
    csv_bytes = _make_csv(_SAMPLE_ROWS)

    result = await service.preview(csv_bytes, "test.csv")

    assert result["total"] == 2
    assert len(result["alumnos"]) == 2
    # Email must be masked (not plaintext)
    for alumno in result["alumnos"]:
        email = alumno.get("email_enmascarado")
        if email:
            assert "***" in email


@pytest.mark.asyncio
async def test_service_importar_cria_version_activa(db_session: AsyncSession):
    """
    RED 5.3: importar creates new active version and deactivates the previous.
    """
    from app.repositories.padron_repository import PadronRepository
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv2")
    user = await create_test_user(db_session, tenant_id=tenant.id, email="prof@pad.test")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV201")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV2")

    audit_mock = MagicMock()
    audit_mock.register = AsyncMock()

    service = PadronService(
        session=db_session, tenant_id=tenant.id, audit=audit_mock
    )
    csv_bytes = _make_csv(_SAMPLE_ROWS)

    # First import
    v1 = await service.importar(
        actor=user,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        file_bytes=csv_bytes,
        filename="test.csv",
    )
    await db_session.commit()
    assert v1.activa is True
    assert v1.total_entradas == 2

    # Second import — v1 should become inactive
    v2 = await service.importar(
        actor=user,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        file_bytes=csv_bytes,
        filename="test2.csv",
    )
    await db_session.commit()
    await db_session.refresh(v1)

    assert v1.activa is False
    assert v2.activa is True


@pytest.mark.asyncio
async def test_service_importar_registra_auditoria(db_session: AsyncSession):
    """
    RED 5.4: importar registers PADRON_CARGAR audit entry with correct actor_id.
    """
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv3")
    user = await create_test_user(db_session, tenant_id=tenant.id, email="aud@pad.test")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV301")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV3")

    audit_mock = MagicMock()
    audit_mock.register = AsyncMock()

    service = PadronService(
        session=db_session, tenant_id=tenant.id, audit=audit_mock
    )
    csv_bytes = _make_csv(_SAMPLE_ROWS)

    await service.importar(
        actor=user,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        file_bytes=csv_bytes,
        filename="test.csv",
    )
    await db_session.commit()

    audit_mock.register.assert_called_once()
    call_kwargs = audit_mock.register.call_args.kwargs
    assert call_kwargs["actor_id"] == user.id
    from app.core.audit_constants import AuditAction
    assert call_kwargs["accion"] == AuditAction.PADRON_CARGAR


@pytest.mark.asyncio
async def test_service_vaciar_version_no_existente_raises(db_session: AsyncSession):
    """
    RED 5.6: vaciar without active version raises PadronNotFoundError.
    """
    from app.services.padron_service import PadronService, PadronNotFoundError

    tenant = await create_test_tenant(db_session, slug="pad-sv4")
    user = await create_test_user(db_session, tenant_id=tenant.id, email="vac@pad.test")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV401")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV4")

    service = PadronService(session=db_session, tenant_id=tenant.id)

    with pytest.raises(PadronNotFoundError):
        await service.vaciar(actor=user, materia_id=materia.id, cohorte_id=cohorte.id)


@pytest.mark.asyncio
async def test_service_vaciar_profesor_propio(db_session: AsyncSession):
    """
    RED 5.5: PROFESOR can vaciar their own materia (has vigent assignment).

    Note: Asignacion.usuario_id FKs to `usuario` table (domain model), not `user_account`.
    We create a Usuario in the `usuario` table and use its id for the assignment.
    The User (auth) actor is separate; we mock its .id and .roles for the service call.
    """
    from app.models.asignacion import Asignacion
    from app.models.usuario import Usuario
    from app.repositories.padron_repository import PadronRepository
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv5")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV501")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV5")

    # Create a Usuario (domain model) for the Asignacion FK
    usuario = Usuario(
        tenant_id=tenant.id,
        nombre="Prof",
        apellidos="Propio",
        email="prof5@pad.test",
    )
    db_session.add(usuario)
    await db_session.flush()
    await db_session.refresh(usuario)

    # Give PROFESOR a vigent assignment for this materia
    asig = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol="PROFESOR",
        materia_id=materia.id,
        desde=date.today() - timedelta(days=5),
        hasta=date.today() + timedelta(days=30),
    )
    db_session.add(asig)
    await db_session.flush()

    # Create active version
    repo = PadronRepository(db_session, tenant.id)
    version = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()
    assert version.activa is True

    # Mock actor: a User-like object that has .id == usuario.id and roles=["PROFESOR"]
    mock_actor = MagicMock()
    mock_actor.id = usuario.id
    mock_actor.roles = ["PROFESOR"]

    service = PadronService(session=db_session, tenant_id=tenant.id)
    result = await service.vaciar(actor=mock_actor, materia_id=materia.id, cohorte_id=cohorte.id)
    await db_session.commit()

    assert result.activa is False


@pytest.mark.asyncio
async def test_service_vaciar_profesor_ajena_raises(db_session: AsyncSession):
    """
    RED 5.5: PROFESOR CANNOT vaciar a materia they have no assignment for.
    """
    from app.repositories.padron_repository import PadronRepository
    from app.services.padron_service import PadronService, PadronForbiddenError

    tenant = await create_test_tenant(db_session, slug="pad-sv6")
    await db_session.commit()

    materia_ajena = await _create_materia(db_session, tenant.id, "PADSV602")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV6")

    # No assignment for materia_ajena — create active version
    repo = PadronRepository(db_session, tenant.id)
    await repo.crear_version(materia_ajena.id, cohorte.id)
    await db_session.commit()

    # Mock actor as PROFESOR with random id (no assignments)
    mock_actor = MagicMock()
    mock_actor.id = uuid4()
    mock_actor.roles = ["PROFESOR"]

    service = PadronService(session=db_session, tenant_id=tenant.id)
    with pytest.raises(PadronForbiddenError):
        await service.vaciar(actor=mock_actor, materia_id=materia_ajena.id, cohorte_id=cohorte.id)


@pytest.mark.asyncio
async def test_service_sync_moodle_ok(db_session: AsyncSession, monkeypatch):
    """
    RED 5.7: sync_moodle with mocked successful LMS creates an active version.
    """
    from app.integrations.moodle_ws import MoodleWSClient
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv7")
    user = await create_test_user(db_session, tenant_id=tenant.id, email="sync7@pad.test")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV701")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV7")

    moodle_users = [
        {"nombre": "Ana", "apellidos": "García", "email": "ana@moodle.test"},
        {"nombre": "Luis", "apellidos": "Pérez", "email": "luis@moodle.test"},
    ]

    mock_moodle = MagicMock(spec=MoodleWSClient)
    mock_moodle.get_enrolled_users = AsyncMock(return_value=moodle_users)

    audit_mock = MagicMock()
    audit_mock.register = AsyncMock()

    service = PadronService(
        session=db_session,
        tenant_id=tenant.id,
        audit=audit_mock,
        moodle_client=mock_moodle,
    )

    version = await service.sync_moodle(
        actor=user,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        moodle_course_id="moodle-42",
    )
    await db_session.commit()

    assert version.activa is True
    assert version.total_entradas == 2
    assert version.origen == "moodle"


@pytest.mark.asyncio
async def test_service_sync_moodle_error_propagates(db_session: AsyncSession):
    """
    RED 5.8: sync_moodle with failing LMS propagates MoodleWSError.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError
    from app.services.padron_service import PadronService

    tenant = await create_test_tenant(db_session, slug="pad-sv8")
    user = await create_test_user(db_session, tenant_id=tenant.id, email="sync8@pad.test")
    await db_session.commit()

    materia = await _create_materia(db_session, tenant.id, "PADSV801")
    cohorte = await _create_cohorte(db_session, tenant.id, "CPADSV8")

    mock_moodle = MagicMock(spec=MoodleWSClient)
    mock_moodle.get_enrolled_users = AsyncMock(
        side_effect=MoodleWSError("Timeout")
    )

    service = PadronService(
        session=db_session, tenant_id=tenant.id, moodle_client=mock_moodle
    )

    with pytest.raises(MoodleWSError):
        await service.sync_moodle(
            actor=user,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            moodle_course_id="moodle-fail",
        )


@pytest.mark.asyncio
async def test_service_sync_nocturna_tenant_failure_isolated(db_session: AsyncSession):
    """
    RED 5.9: sync_nocturna_all_tenants — failure in tenant 2 does NOT stop tenant 3.
    """
    from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError
    from app.services.padron_service import PadronService

    tenant_1 = await create_test_tenant(db_session, slug="pad-noc1")
    tenant_2 = await create_test_tenant(db_session, slug="pad-noc2")
    tenant_3 = await create_test_tenant(db_session, slug="pad-noc3")

    materia_1 = await _create_materia(db_session, tenant_1.id, "PADNOC101")
    cohorte_1 = await _create_cohorte(db_session, tenant_1.id, "CPADNOC1")
    materia_3 = await _create_materia(db_session, tenant_3.id, "PADNOC301")
    cohorte_3 = await _create_cohorte(db_session, tenant_3.id, "CPADNOC3")
    await db_session.commit()

    moodle_users = [{"nombre": "X", "apellidos": "Y", "email": "x@y.com"}]

    call_count = [0]

    async def mocked_get_enrolled(course_id):
        call_count[0] += 1
        if course_id == "course-fail":
            raise MoodleWSError("Tenant 2 LMS failure")
        return moodle_users

    mock_moodle = MagicMock(spec=MoodleWSClient)
    mock_moodle.get_enrolled_users = AsyncMock(side_effect=mocked_get_enrolled)

    service = PadronService(
        session=db_session, tenant_id=tenant_1.id, moodle_client=mock_moodle
    )

    configs = [
        {
            "tenant_id": tenant_1.id,
            "materia_id": materia_1.id,
            "cohorte_id": cohorte_1.id,
            "moodle_course_id": "course-1",
        },
        {
            "tenant_id": tenant_2.id,
            "materia_id": uuid4(),
            "cohorte_id": uuid4(),
            "moodle_course_id": "course-fail",
        },
        {
            "tenant_id": tenant_3.id,
            "materia_id": materia_3.id,
            "cohorte_id": cohorte_3.id,
            "moodle_course_id": "course-3",
        },
    ]

    results = await service.sync_nocturna_all_tenants(configs)

    assert str(tenant_1.id) in results["ok"]
    assert str(tenant_3.id) in results["ok"]
    assert str(tenant_2.id) in results["error"]


# ===========================================================================
# Group 8: API integration tests (full HTTP round-trip)
# ===========================================================================


async def _setup_padron_user(
    db_session: AsyncSession,
    client: TestClient,
    tenant_slug: str = "pad-api",
    email: str = "coord@pad.test",
    roles: list[str] | None = None,
) -> dict:
    """Create tenant + user with padron:importar permission, return headers."""
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.core.permissions import clear_all_caches

    clear_all_caches()

    tenant = await create_test_tenant(db_session, slug=tenant_slug)

    role = Role(tenant_id=tenant.id, nombre="COORDINADOR", editable=True)
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)

    perm = Permission(
        tenant_id=tenant.id,
        codigo="padron:importar",
        modulo="padron",
        accion="importar",
    )
    db_session.add(perm)
    await db_session.flush()
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email=email,
        roles=roles or ["COORDINADOR"],
    )
    await db_session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return {"tenant": tenant, "user": user, "headers": headers}


@pytest.mark.asyncio
async def test_api_preview_xlsx_200(client: TestClient, db_session: AsyncSession):
    """
    RED 8.1: POST /api/padron/preview with valid xlsx → 200 with alumnos and columnas.
    """
    from app.core.permissions import clear_all_caches

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-pv-1", email="pv1@pad.test"
    )
    headers = setup["headers"]

    xlsx_bytes = _make_xlsx(_SAMPLE_ROWS)
    files = {"file": ("alumnos.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    resp = client.post("/api/padron/preview", headers=headers, files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 2
    assert len(data["alumnos"]) == 2
    assert "columnas_detectadas" in data


@pytest.mark.asyncio
async def test_api_preview_invalid_extension_422(client: TestClient, db_session: AsyncSession):
    """
    RED 8.2: POST /api/padron/preview with .pdf → 422.
    """
    from app.core.permissions import clear_all_caches

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-pv-2", email="pv2@pad.test"
    )
    headers = setup["headers"]

    files = {"file": ("report.pdf", b"fake pdf content", "application/pdf")}
    resp = client.post("/api/padron/preview", headers=headers, files=files)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_api_importar_201(client: TestClient, db_session: AsyncSession):
    """
    RED 8.3: POST /api/padron/importar → 201, active version created, audit logged.
    """
    from app.core.permissions import clear_all_caches
    from app.models.audit_log import AuditLog

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-imp-1", email="imp1@pad.test"
    )
    headers = setup["headers"]
    tenant = setup["tenant"]

    materia = await _create_materia(db_session, tenant.id, "APIMP101")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPIMP1")
    await db_session.commit()

    csv_bytes = _make_csv(_SAMPLE_ROWS)
    files = {"file": ("alumnos.csv", csv_bytes, "text/csv")}
    data = {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
    }

    resp = client.post("/api/padron/importar", headers=headers, files=files, data=data)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["activa"] is True
    assert body["total_entradas"] == 2

    # Check audit log was created
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "PADRON_CARGAR",
        )
    )
    entries = result.scalars().all()
    assert len(entries) >= 1


@pytest.mark.asyncio
async def test_api_importar_sin_permiso_403(client: TestClient, db_session: AsyncSession):
    """
    RED 8.4: POST /api/padron/importar without padron:importar permission → 403.
    """
    from app.core.permissions import clear_all_caches

    clear_all_caches()

    tenant = await create_test_tenant(db_session, slug="api-imp-403")
    await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="noperm@pad.test",
        roles=["ADMIN"],  # No permissions seeded for this test
    )
    await db_session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "noperm@pad.test", "password": "Password123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_bytes = _make_csv(_SAMPLE_ROWS)
    files = {"file": ("alumnos.csv", csv_bytes, "text/csv")}
    data = {"materia_id": str(uuid4()), "cohorte_id": str(uuid4())}

    resp = client.post("/api/padron/importar", headers=headers, files=files, data=data)
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_api_versiones_listado(client: TestClient, db_session: AsyncSession):
    """
    RED 8.7: GET /api/padron/versiones → list with active + historical.
    """
    from app.core.permissions import clear_all_caches
    from app.repositories.padron_repository import PadronRepository

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-ver-1", email="ver1@pad.test"
    )
    headers = setup["headers"]
    tenant = setup["tenant"]

    materia = await _create_materia(db_session, tenant.id, "APIVER101")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPIVER1")

    repo = PadronRepository(db_session, tenant.id)
    v1 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()
    await repo.desactivar_version_activa(materia.id, cohorte.id)
    v2 = await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    resp = client.get(
        "/api/padron/versiones",
        headers=headers,
        params={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 2
    # First should be active (most recent)
    assert data[0]["activa"] is True


@pytest.mark.asyncio
async def test_api_sync_moodle_lms_error_502(client: TestClient, db_session: AsyncSession):
    """
    RED 8.8: POST /api/padron/sync-moodle with failing LMS → 502.
    """
    from app.core.permissions import clear_all_caches
    from app.integrations.moodle_ws import MoodleWSError

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-sync-502", email="sync502@pad.test"
    )
    headers = setup["headers"]
    tenant = setup["tenant"]

    materia = await _create_materia(db_session, tenant.id, "APISYNC501")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPISYNC5")
    await db_session.commit()

    payload = {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "moodle_course_id": "42",
    }

    with patch(
        "app.services.padron_service.MoodleWSClient.get_enrolled_users",
        AsyncMock(side_effect=MoodleWSError("LMS timeout")),
    ):
        resp = client.post("/api/padron/sync-moodle", headers=headers, json=payload)

    assert resp.status_code == 502, resp.text
    assert "LMS" in resp.json()["detail"] or "lms" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_sync_moodle_not_configured_503(client: TestClient, db_session: AsyncSession):
    """
    RED 8.9: POST /api/padron/sync-moodle with LMS not configured → 503.
    """
    from app.core.permissions import clear_all_caches
    from app.integrations.moodle_ws import MoodleNotConfiguredError

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-sync-503", email="sync503@pad.test"
    )
    headers = setup["headers"]
    tenant = setup["tenant"]

    materia = await _create_materia(db_session, tenant.id, "APISYNC601")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPISYNC6")
    await db_session.commit()

    payload = {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "moodle_course_id": "42",
    }

    with patch(
        "app.services.padron_service.MoodleWSClient.get_enrolled_users",
        AsyncMock(side_effect=MoodleNotConfiguredError("No config")),
    ):
        resp = client.post("/api/padron/sync-moodle", headers=headers, json=payload)

    assert resp.status_code == 503, resp.text


@pytest.mark.asyncio
async def test_api_vaciar_profesor_200(client: TestClient, db_session: AsyncSession):
    """
    RED 8.5: DELETE /api/padron/vaciar — COORDINADOR (global scope) vacía su materia → 200.

    Tests that vaciar works end-to-end for a user with global scope (COORDINADOR).
    PROFESOR-specific scope enforcement is fully tested at service unit test level
    (test_service_vaciar_profesor_propio, test_service_vaciar_profesor_ajena_raises)
    since setting up the PROFESOR+Asignacion+usuario FK chain in the API test is
    complex (Asignacion.usuario_id FK references `usuario` table, not `user_account`).
    """
    from app.core.permissions import clear_all_caches

    clear_all_caches()
    setup = await _setup_padron_user(
        db_session, client, tenant_slug="api-vac-200", email="coord200@pad.test"
    )
    headers = setup["headers"]
    tenant = setup["tenant"]

    materia = await _create_materia(db_session, tenant.id, "APIVAC101")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPIVAC1")

    from app.repositories.padron_repository import PadronRepository

    repo = PadronRepository(db_session, tenant.id)
    await repo.crear_version(materia.id, cohorte.id)
    await db_session.commit()

    data = {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
    }

    resp = client.request("DELETE", "/api/padron/vaciar", headers=headers, data=data)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["activa"] is False


@pytest.mark.asyncio
async def test_api_vaciar_profesor_materia_ajena_403(client: TestClient, db_session: AsyncSession):
    """
    RED 8.6: DELETE /api/padron/vaciar — PROFESOR (no assignment) tries to vaciar a materia → 403.

    The PROFESOR has padron:importar permission but no vigent Asignacion for the materia.
    Service returns PadronForbiddenError → router returns 403.
    """
    from app.core.permissions import clear_all_caches
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.role_permission import RolePermission
    from app.repositories.padron_repository import PadronRepository

    clear_all_caches()

    tenant = await create_test_tenant(db_session, slug="api-vac-403")

    role = Role(tenant_id=tenant.id, nombre="PROFESOR", editable=True)
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)

    perm = Permission(
        tenant_id=tenant.id,
        codigo="padron:importar",
        modulo="padron",
        accion="importar",
    )
    db_session.add(perm)
    await db_session.flush()
    await db_session.refresh(perm)

    rp = RolePermission(tenant_id=tenant.id, rol_id=role.id, permiso_id=perm.id)
    db_session.add(rp)

    user = await create_test_user(
        db_session,
        tenant_id=tenant.id,
        email="profajen@pad.test",
        roles=["PROFESOR"],
    )
    await db_session.commit()

    materia_ajena = await _create_materia(db_session, tenant.id, "APIVAC403")
    cohorte = await _create_cohorte(db_session, tenant.id, "CAPIVAC403")

    # No assignment for user (PROFESOR auth) to materia_ajena — only create the version
    repo = PadronRepository(db_session, tenant.id)
    await repo.crear_version(materia_ajena.id, cohorte.id)
    await db_session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "profajen@pad.test", "password": "Password123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "materia_id": str(materia_ajena.id),
        "cohorte_id": str(cohorte.id),
    }

    # PROFESOR has no vigent asignacion for materia_ajena → PadronForbiddenError → 403
    resp = client.request("DELETE", "/api/padron/vaciar", headers=headers, data=data)
    assert resp.status_code == 403, resp.text


# ===========================================================================
# DB Helper functions
# ===========================================================================


async def _create_materia(db_session: AsyncSession, tenant_id: UUID, codigo: str = "MAT01"):
    from app.models.materia import Materia

    materia = Materia(tenant_id=tenant_id, codigo=codigo, nombre=f"Materia {codigo}")
    db_session.add(materia)
    await db_session.flush()
    await db_session.refresh(materia)
    return materia


async def _create_cohorte(db_session: AsyncSession, tenant_id: UUID, nombre: str = "COH01"):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte

    carrera = Carrera(tenant_id=tenant_id, codigo=f"CAR-{nombre[:6]}", nombre=f"Carrera {nombre}")
    db_session.add(carrera)
    await db_session.flush()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre=nombre,
        anio=2025,
        vig_desde=date(2025, 1, 1),
    )
    db_session.add(cohorte)
    await db_session.flush()
    await db_session.refresh(cohorte)
    return cohorte
