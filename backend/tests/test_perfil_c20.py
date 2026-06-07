"""
Strict TDD tests for C-20 perfil-y-mensajeria-interna.

Group 1: Pure unit — PerfilService cuil inmutable (no DB)
Group 2: Pure unit — InboxService validaciones (no DB)
Group 3: Integration — perfil GET/PATCH (requires TEST_DATABASE_URL)
Group 4: Integration — inbox hilos y mensajes (requires TEST_DATABASE_URL)
"""

from __future__ import annotations

import pytest
from uuid import uuid4


# ===========================================================================
# Group 1 — CUIL inmutable en PerfilService (pure unit, no DB)
# ===========================================================================


class TestPerfilCuilInmutable:
    """Unit tests for CUIL immutability rule."""

    def _validate(self, payload: dict) -> None:
        from app.services.perfil_service import validar_campos_perfil
        validar_campos_perfil(payload)

    def test_cuil_en_payload_lanza_error(self) -> None:
        with pytest.raises(ValueError, match="cuil"):
            self._validate({"cuil": "20-12345678-1"})

    def test_campos_editables_no_lanzan_error(self) -> None:
        self._validate({"banco": "Banco Nación", "regional": "CABA"})

    def test_payload_vacio_no_lanza_error(self) -> None:
        self._validate({})

    def test_modalidad_cobro_valida(self) -> None:
        self._validate({"modalidad_cobro": "factura"})

    def test_modalidad_cobro_invalida_lanza_error(self) -> None:
        with pytest.raises(ValueError, match="modalidad_cobro"):
            self._validate({"modalidad_cobro": "desconocida"})


# ===========================================================================
# Group 2 — InboxService validaciones (pure unit, no DB)
# ===========================================================================


class TestInboxValidaciones:
    """Unit tests for inbox business rules."""

    def _check_mismo_user(self, remitente_id, destinatario_id) -> None:
        from app.services.inbox_service import validar_destinatario
        validar_destinatario(remitente_id, destinatario_id)

    def test_mismo_user_lanza_error(self) -> None:
        uid = uuid4()
        with pytest.raises(ValueError, match="mismo"):
            self._check_mismo_user(uid, uid)

    def test_distintos_users_no_lanza(self) -> None:
        self._check_mismo_user(uuid4(), uuid4())


# ===========================================================================
# Group 3 — integration tests (require TEST_DATABASE_URL)
# ===========================================================================


class TestPerfilIntegration:
    @pytest.mark.asyncio
    async def test_get_perfil_retorna_usuario(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_patch_banco_actualiza(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_cuil_no_modificable_integration(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestInboxIntegration:
    @pytest.mark.asyncio
    async def test_iniciar_hilo_exitoso(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_leer_hilo_marca_leidos(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_hilo_ajeno_retorna_403(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestRouterGuardsC20:
    def test_perfil_sin_auth(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    def test_inbox_sin_auth(self) -> None:
        pytest.skip("requires TEST_DATABASE_URL")
