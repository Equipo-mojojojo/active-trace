"""
Strict TDD tests for C-12 comunicaciones-cola-worker.

TDD cycle:
  Group 1: State machine (pure unit, no DB) — model state transitions
  Group 2: Service preview/template (pure unit, no DB) — template rendering
  Group 3: Preview token (pure unit, no DB) — HMAC token lifecycle
  Group 4: Worker unit (pure unit, mocked repo) — loop and retry logic
  Group 5: Repository integration (requires TEST_DATABASE_URL)
  Group 6: API tests (requires TEST_DATABASE_URL)
  Group 7: Security tests (requires TEST_DATABASE_URL)

RED → GREEN → TRIANGULATE → REFACTOR order preserved.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from tests.conftest import create_test_tenant, create_test_user, create_test_materia


# ===========================================================================
# Group 1 — State machine (pure unit, no DB)
# ===========================================================================
# RED: import fails until models/comunicacion.py and models/enums.py exist.


class TestEstadoComunicacion:
    """Unit tests for Comunicacion state machine (D1)."""

    def setup_method(self):
        from app.models.comunicacion import Comunicacion, InvalidStateTransitionError
        from app.models.enums import EstadoComunicacion

        self.Comunicacion = Comunicacion
        self.StateError = InvalidStateTransitionError
        self.Estado = EstadoComunicacion

    def _make(self, estado=None):
        """Instantiate Comunicacion in-memory without DB session."""
        from uuid import uuid4

        c = self.Comunicacion(
            tenant_id=uuid4(),
            enviado_por=uuid4(),
            materia_id=uuid4(),
            destinatario="test@example.com",
            asunto="test",
            cuerpo="test",
        )
        if estado is not None:
            c.estado = estado
        return c

    # ── Valid transitions ────────────────────────────────────────────

    def test_pendiente_to_enviando_valid(self):
        c = self._make(self.Estado.PENDIENTE)
        c.marcar_enviando()
        assert c.estado == self.Estado.ENVIANDO

    def test_enviando_to_enviado_valid(self):
        c = self._make(self.Estado.ENVIANDO)
        c.marcar_enviado()
        assert c.estado == self.Estado.ENVIADO

    def test_enviando_to_error_valid(self):
        c = self._make(self.Estado.ENVIANDO)
        c.marcar_error()
        assert c.estado == self.Estado.ERROR

    def test_pendiente_to_cancelado_valid(self):
        c = self._make(self.Estado.PENDIENTE)
        c.cancelar()
        assert c.estado == self.Estado.CANCELADO

    # ── Invalid transitions (triangulate) ───────────────────────────

    def test_enviado_to_enviando_invalid(self):
        c = self._make(self.Estado.ENVIADO)
        with pytest.raises(self.StateError):
            c.marcar_enviando()

    def test_cancelado_to_enviando_invalid(self):
        c = self._make(self.Estado.CANCELADO)
        with pytest.raises(self.StateError):
            c.marcar_enviando()

    def test_error_to_enviando_invalid(self):
        c = self._make(self.Estado.ERROR)
        with pytest.raises(self.StateError):
            c.marcar_enviando()

    def test_enviando_to_cancelado_invalid(self):
        """cancelar() only valid from PENDIENTE."""
        c = self._make(self.Estado.ENVIANDO)
        with pytest.raises(self.StateError):
            c.cancelar()

    def test_enviado_to_cancelado_invalid(self):
        c = self._make(self.Estado.ENVIADO)
        with pytest.raises(self.StateError):
            c.cancelar()

    # ── Spec: marcar_enviado registra enviado_at ─────────────────────

    def test_marcar_enviado_sets_enviado_at(self):
        c = self._make(self.Estado.ENVIANDO)
        before = datetime.now(timezone.utc)
        c.marcar_enviado()
        assert c.enviado_at is not None
        assert c.enviado_at >= before

    def test_marcar_enviado_from_pendiente_invalid(self):
        c = self._make(self.Estado.PENDIENTE)
        with pytest.raises(self.StateError):
            c.marcar_enviado()

    def test_marcar_error_from_pendiente_invalid(self):
        c = self._make(self.Estado.PENDIENTE)
        with pytest.raises(self.StateError):
            c.marcar_error()


# ===========================================================================
# Group 2 — Service preview / template rendering (pure unit, no DB)
# ===========================================================================
# RED: import fails until services/comunicacion_service.py exists.


class TestTemplateRendering:
    """Unit tests for _render_template() — D5."""

    def setup_method(self):
        from app.services.comunicacion_service import (
            ComunicacionService,
            VariableDesconocidaError,
        )

        self.service = ComunicacionService.__new__(ComunicacionService)
        self.VariableError = VariableDesconocidaError

    def test_render_single_variable(self):
        result = self.service._render_template(
            "Hola {nombre_alumno}", {"nombre_alumno": "Ana García"}
        )
        assert result == "Hola Ana García"

    def test_render_multiple_variables(self):
        result = self.service._render_template(
            "{nombre_alumno} cursa {materia} con {docente}",
            {"nombre_alumno": "Ana", "materia": "Matemática", "docente": "Prof. López"},
        )
        assert result == "Ana cursa Matemática con Prof. López"

    def test_unknown_variable_raises(self):
        with pytest.raises(self.VariableError, match="variable_inexistente"):
            self.service._render_template(
                "Hola {variable_inexistente}", {"nombre_alumno": "Ana"}
            )

    def test_empty_template_returns_empty(self):
        result = self.service._render_template("", {})
        assert result == ""

    def test_template_without_variables_unchanged(self):
        result = self.service._render_template("Mensaje sin variables", {})
        assert result == "Mensaje sin variables"


# ===========================================================================
# Group 3 — Preview token lifecycle (pure unit, no DB)
# ===========================================================================


class TestPreviewToken:
    """Unit tests for _generate_preview_token / _validate_preview_token."""

    def setup_method(self):
        import os

        os.environ.setdefault(
            "SECRET_KEY", "test-secret-key-with-at-least-32-characters"
        )
        os.environ.setdefault(
            "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
        )
        os.environ.setdefault("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef")
        os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "10080")
        os.environ.setdefault("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
        os.environ.setdefault("TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES", "5")
        os.environ.setdefault("TOTP_ISSUER", "test")
        os.environ.setdefault("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5")
        os.environ.setdefault("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
        os.environ.setdefault("OTEL_ENABLED", "false")

        from app.core.config import get_settings

        get_settings.cache_clear()

        from app.services.comunicacion_service import (
            ComunicacionService,
            PreviewExpiredError,
            PreviewRequiredError,
        )

        self.service = ComunicacionService.__new__(ComunicacionService)
        self.PreviewExpiredError = PreviewExpiredError
        self.PreviewRequiredError = PreviewRequiredError

    def test_valid_token_validates_without_error(self):
        token = self.service._generate_preview_token("asunto", "cuerpo")
        self.service._validate_preview_token(token, "asunto", "cuerpo")

    def test_none_token_raises_required_error(self):
        with pytest.raises(self.PreviewRequiredError):
            self.service._validate_preview_token(None, "asunto", "cuerpo")

    def test_expired_token_raises_expired_error(self):
        token = self.service._generate_preview_token(
            "asunto", "cuerpo", issued_at_override=time.time() - 700
        )
        with pytest.raises(self.PreviewExpiredError):
            self.service._validate_preview_token(token, "asunto", "cuerpo")

    def test_changed_asunto_raises_required_error(self):
        token = self.service._generate_preview_token("asunto original", "cuerpo")
        with pytest.raises(self.PreviewRequiredError):
            self.service._validate_preview_token(token, "asunto modificado", "cuerpo")

    def test_changed_cuerpo_raises_required_error(self):
        token = self.service._generate_preview_token("asunto", "cuerpo original")
        with pytest.raises(self.PreviewRequiredError):
            self.service._validate_preview_token(token, "asunto", "cuerpo modificado")

    def test_tampered_token_raises_required_error(self):
        with pytest.raises(self.PreviewRequiredError):
            self.service._validate_preview_token("token-invalido", "asunto", "cuerpo")


# ===========================================================================
# Group 4 — Worker unit (pure unit, mocked repo)
# ===========================================================================


class TestComunicacionWorkerUnit:
    """Unit tests for worker logic — mocked DB session."""

    def setup_method(self):
        from app.models.comunicacion import Comunicacion, InvalidStateTransitionError
        from app.models.enums import EstadoComunicacion
        from app.workers.comunicacion_worker import ComunicacionWorker

        self.Comunicacion = Comunicacion
        self.Estado = EstadoComunicacion
        self.Worker = ComunicacionWorker
        self.StateError = InvalidStateTransitionError

    def _make_comunicacion(self, estado=None):
        c = self.Comunicacion(
            tenant_id=uuid4(),
            enviado_por=uuid4(),
            materia_id=uuid4(),
            destinatario="test@example.com",
            asunto="test",
            cuerpo="test",
            reintento_count=0,
        )
        if estado is not None:
            c.estado = estado
        return c

    @pytest.mark.asyncio
    async def test_process_pendiente_to_enviado(self):
        worker = self.Worker.__new__(self.Worker)
        worker._max_retries = 3

        c = self._make_comunicacion(self.Estado.PENDIENTE)
        c.marcar_enviando()

        send_called = []

        async def mock_send(com):
            send_called.append(com.id)

        worker._enviar_mock = mock_send
        await worker._attempt_send(c, mock_send)

        assert c.estado == self.Estado.ENVIADO
        assert len(send_called) == 1

    @pytest.mark.asyncio
    async def test_process_fail_marks_error(self):
        worker = self.Worker.__new__(self.Worker)
        worker._max_retries = 1

        c = self._make_comunicacion(self.Estado.ENVIANDO)

        async def failing_send(com):
            raise RuntimeError("send failed")

        await worker._attempt_send(c, failing_send)

        assert c.estado == self.Estado.ERROR
        assert c.reintento_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self):
        worker = self.Worker.__new__(self.Worker)
        worker._max_retries = 3

        c = self._make_comunicacion(self.Estado.ENVIANDO)
        attempts = []

        async def flaky_send(com):
            attempts.append(1)
            if len(attempts) == 1:
                raise RuntimeError("first attempt failed")

        await worker._attempt_send(c, flaky_send, base_delay=0)

        assert c.estado == self.Estado.ENVIADO
        assert c.reintento_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_marks_error(self):
        worker = self.Worker.__new__(self.Worker)
        worker._max_retries = 3

        c = self._make_comunicacion(self.Estado.ENVIANDO)

        async def always_fail(com):
            raise RuntimeError("always fails")

        await worker._attempt_send(c, always_fail, base_delay=0)

        assert c.estado == self.Estado.ERROR
        assert c.reintento_count == 3


# ===========================================================================
# Group 5 — Repository integration (requires TEST_DATABASE_URL)
# ===========================================================================


@pytest.mark.asyncio
class TestComunicacionRepository:
    """Integration tests for ComunicacionRepository."""

    async def test_crear_encrypts_destinatario(
        self, db_session, test_tenant, test_materia
    ):
        """destinatario column must contain ciphertext, not plain email."""
        from sqlalchemy import text

        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        usuario = Usuario(
            tenant_id=test_tenant.id,
            nombre="Remit",
            apellidos="Ente",
            email="remitente@test.com",
        )
        db_session.add(usuario)
        await db_session.flush()

        repo = ComunicacionRepository(db_session, test_tenant.id)
        com = await repo.crear(
            tenant_id=test_tenant.id,
            enviado_por=usuario.id,
            materia_id=test_materia.id,
            destinatario="alumno@test.com",
            asunto="Test encrypt",
            cuerpo="Cuerpo",
        )
        await db_session.flush()

        row = (
            await db_session.execute(
                text("SELECT destinatario FROM comunicacion WHERE id = :id"),
                {"id": str(com.id)},
            )
        ).fetchone()
        assert row is not None
        assert row[0] != "alumno@test.com"
        assert len(row[0]) > 20

    async def test_listar_por_lote_returns_only_matching(
        self, db_session, test_tenant, test_materia
    ):
        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        usuario = Usuario(
            tenant_id=test_tenant.id,
            nombre="Doc",
            apellidos="Lote",
            email="doclote@test.com",
        )
        db_session.add(usuario)
        await db_session.flush()

        repo = ComunicacionRepository(db_session, test_tenant.id)
        lote_id = uuid4()

        for i in range(3):
            await repo.crear(
                tenant_id=test_tenant.id,
                enviado_por=usuario.id,
                materia_id=test_materia.id,
                destinatario=f"a{i}@test.com",
                asunto="Lote test",
                cuerpo="Body",
                lote_id=lote_id,
            )
        # One message with a different lote
        await repo.crear(
            tenant_id=test_tenant.id,
            enviado_por=usuario.id,
            materia_id=test_materia.id,
            destinatario="other@test.com",
            asunto="Other",
            cuerpo="Body",
            lote_id=uuid4(),
        )
        await db_session.flush()

        items = await repo.listar_por_lote(lote_id)
        assert len(items) == 3

    async def test_tenant_isolation_repo(
        self, db_session, test_materia
    ):
        """Repo for tenant B sees zero messages created by tenant A."""
        from app.models.materia import Materia
        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        tenant_a = await create_test_tenant(db_session, slug="ta-c12", name="C12 A")
        await db_session.commit()
        tenant_b = await create_test_tenant(db_session, slug="tb-c12", name="C12 B")
        await db_session.commit()

        ua = Usuario(
            tenant_id=tenant_a.id, nombre="A", apellidos="User", email="ua-c12@test.com"
        )
        db_session.add(ua)
        await db_session.flush()

        mat_a = Materia(
            tenant_id=tenant_a.id, codigo="MAT-C12A", nombre="Materia C12 A"
        )
        db_session.add(mat_a)
        await db_session.flush()

        repo_a = ComunicacionRepository(db_session, tenant_a.id)
        await repo_a.crear(
            tenant_id=tenant_a.id,
            enviado_por=ua.id,
            materia_id=mat_a.id,
            destinatario="dest@test.com",
            asunto="Isolation test",
            cuerpo="Body",
        )
        await db_session.flush()

        repo_b = ComunicacionRepository(db_session, tenant_b.id)
        items_b = await repo_b.listar_por_estado_pendiente()
        assert len(items_b) == 0

    async def test_aprobar_lote_sets_aprobado_por(
        self, db_session, test_tenant, test_materia
    ):
        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        usuario = Usuario(
            tenant_id=test_tenant.id,
            nombre="Aprob",
            apellidos="Ador",
            email="aprobador@test.com",
        )
        db_session.add(usuario)
        await db_session.flush()

        repo = ComunicacionRepository(db_session, test_tenant.id)
        lote_id = uuid4()
        for _ in range(2):
            await repo.crear(
                tenant_id=test_tenant.id,
                enviado_por=usuario.id,
                materia_id=test_materia.id,
                destinatario="a@test.com",
                asunto="Aprobacion",
                cuerpo="Body",
                lote_id=lote_id,
            )
        await db_session.flush()

        count = await repo.aprobar_lote(lote_id, aprobado_por=usuario.id)
        await db_session.flush()

        assert count == 2
        items = await repo.listar_por_lote(lote_id)
        for item in items:
            assert item.aprobado_por == usuario.id


# ===========================================================================
# Group 6 — API tests (requires TEST_DATABASE_URL)
# ===========================================================================


def test_preview_sin_auth_retorna_401(client):
    """Preview endpoint rejects unauthenticated requests."""
    resp = client.post(
        "/api/v1/comunicaciones/preview",
        json={"asunto": "Test", "cuerpo": "Test", "variables": {}},
    )
    assert resp.status_code == 401


def test_enviar_sin_auth_retorna_401(client):
    resp = client.post(
        "/api/v1/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Test",
            "destinatarios": [],
            "materia_id": str(uuid4()),
            "preview_token": "tok",
        },
    )
    assert resp.status_code == 401


# ===========================================================================
# Group 7 — Security tests (requires TEST_DATABASE_URL)
# ===========================================================================


@pytest.mark.asyncio
class TestComunicacionSecurity:
    """Security: PII encryption, log redaction, identity from JWT."""

    async def test_destinatario_cifrado_en_db(
        self, db_session, test_tenant, test_materia
    ):
        """Raw DB value for destinatario must not equal plain email."""
        from sqlalchemy import text

        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        usuario = Usuario(
            tenant_id=test_tenant.id,
            nombre="Sec",
            apellidos="Tester",
            email="sec7@test.com",
        )
        db_session.add(usuario)
        await db_session.flush()

        repo = ComunicacionRepository(db_session, test_tenant.id)
        await repo.crear(
            tenant_id=test_tenant.id,
            enviado_por=usuario.id,
            materia_id=test_materia.id,
            destinatario="secret-pii@alumno.com",
            asunto="Security test",
            cuerpo="Body",
        )
        await db_session.flush()

        raw = (
            await db_session.execute(
                text(
                    "SELECT destinatario FROM comunicacion WHERE asunto = 'Security test' LIMIT 1"
                )
            )
        ).fetchone()
        assert raw[0] != "secret-pii@alumno.com"

    async def test_pii_ausente_en_logs(
        self, db_session, test_tenant, test_materia, caplog
    ):
        """Email destinatario must not appear in any log output."""
        import logging

        from app.models.usuario import Usuario
        from app.repositories.comunicacion_repository import ComunicacionRepository

        usuario = Usuario(
            tenant_id=test_tenant.id,
            nombre="Log",
            apellidos="Tester",
            email="logtest7@test.com",
        )
        db_session.add(usuario)
        await db_session.flush()

        repo = ComunicacionRepository(db_session, test_tenant.id)
        with caplog.at_level(logging.DEBUG):
            await repo.crear(
                tenant_id=test_tenant.id,
                enviado_por=usuario.id,
                materia_id=test_materia.id,
                destinatario="do-not-log@secret.com",
                asunto="Log security test",
                cuerpo="Body",
            )
            await db_session.flush()

        assert "do-not-log@secret.com" not in caplog.text
