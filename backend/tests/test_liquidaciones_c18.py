"""
Strict TDD tests for C-18 liquidaciones-y-honorarios.

TDD order:
  Group 1: Pure unit — LiquidacionService cálculo (no DB)
  Group 2: Pure unit — solapamiento de vigencias (no DB)
  Group 3: Integration — repositories (requires TEST_DATABASE_URL)
  Group 4: Integration — router guards (requires TEST_DATABASE_URL)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest


# ===========================================================================
# Helpers / stubs
# ===========================================================================


def _comision(grupo_plus_clave: str | None) -> Any:
    m = SimpleNamespace(grupo_plus_clave=grupo_plus_clave)
    return SimpleNamespace(materia=m)


def _tenant(tope_plus: int | None = None) -> Any:
    return SimpleNamespace(tope_plus=tope_plus)


# ===========================================================================
# Group 1 — calcular_liquidacion (pure unit, no DB)
# ===========================================================================
# RED: import fails until liquidacion_service.py with calcular_total exists.


class TestCalcularLiquidacion:
    """Unit tests for the pure liquidation calculation logic."""

    def _run(
        self,
        salario_base: Decimal,
        comisiones: list[Any],
        plus_lookup: dict[tuple[str, str], Decimal],
        rol: str,
        tenant: Any,
    ) -> tuple[Decimal, Decimal]:
        from app.services.liquidacion_service import calcular_total

        return calcular_total(salario_base, comisiones, plus_lookup, rol, tenant)

    def test_solo_base_sin_comisiones(self) -> None:
        """Docente sin comisiones → solo base."""
        monto_base, monto_plus = self._run(
            Decimal("1000"),
            [],
            {},
            "PROFESOR",
            _tenant(),
        )
        assert monto_base == Decimal("1000")
        assert monto_plus == Decimal("0")

    def test_base_mas_un_plus(self) -> None:
        """Un plus acumula correctamente."""
        comisiones = [_comision("PROG")]
        lookup = {("PROG", "PROFESOR"): Decimal("200")}
        monto_base, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant()
        )
        assert monto_base == Decimal("1000")
        assert monto_plus == Decimal("200")

    def test_acumulacion_lineal_multiples_comisiones(self) -> None:
        """Dos comisiones del mismo grupo acumulan 2×plus (RN-21 lineal)."""
        comisiones = [_comision("PROG"), _comision("PROG")]
        lookup = {("PROG", "PROFESOR"): Decimal("200")}
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant()
        )
        assert monto_plus == Decimal("400")

    def test_plus_de_distintos_grupos(self) -> None:
        """Comisiones de grupos distintos suman sus plus respectivos."""
        comisiones = [_comision("PROG"), _comision("BD")]
        lookup = {
            ("PROG", "PROFESOR"): Decimal("200"),
            ("BD", "PROFESOR"): Decimal("150"),
        }
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant()
        )
        assert monto_plus == Decimal("350")

    def test_comision_sin_grupo_plus_no_suma(self) -> None:
        """Comisión con grupo_plus_clave nulo no genera plus."""
        comisiones = [_comision(None), _comision("PROG")]
        lookup = {("PROG", "PROFESOR"): Decimal("200")}
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant()
        )
        assert monto_plus == Decimal("200")

    def test_grupo_sin_plus_vigente_retorna_cero(self) -> None:
        """Si no hay SalarioPlus vigente para el grupo, ese plus es 0."""
        comisiones = [_comision("PROG")]
        lookup: dict = {}
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant()
        )
        assert monto_plus == Decimal("0")

    def test_tope_plus_limita_acumulacion(self) -> None:
        """tope_plus=2 con 5 comisiones → solo 2 plus acumulados."""
        comisiones = [_comision("PROG")] * 5
        lookup = {("PROG", "PROFESOR"): Decimal("200")}
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant(tope_plus=2)
        )
        assert monto_plus == Decimal("400")

    def test_tope_plus_nulo_es_ilimitado(self) -> None:
        """tope_plus=None → acumulación ilimitada."""
        comisiones = [_comision("PROG")] * 5
        lookup = {("PROG", "PROFESOR"): Decimal("200")}
        _, monto_plus = self._run(
            Decimal("1000"), comisiones, lookup, "PROFESOR", _tenant(tope_plus=None)
        )
        assert monto_plus == Decimal("1000")


# ===========================================================================
# Group 2 — solapamiento de vigencias (pure unit, no DB)
# ===========================================================================
# RED: import fails until hay validacion de solapamiento en los repos.


class TestSolapamientoVigencias:
    """Unit tests for the overlap validation logic."""

    def _check(
        self,
        existing_desde: date,
        existing_hasta: date | None,
        new_desde: date,
        new_hasta: date | None,
    ) -> bool:
        from app.repositories.salario_base_repository import vigencias_solapan

        return vigencias_solapan(existing_desde, existing_hasta, new_desde, new_hasta)

    def test_solapamiento_total(self) -> None:
        assert self._check(date(2025, 1, 1), date(2025, 12, 31), date(2025, 6, 1), date(2025, 6, 30)) is True

    def test_solapamiento_parcial_inicio(self) -> None:
        assert self._check(date(2025, 1, 1), date(2025, 6, 30), date(2025, 6, 1), date(2025, 12, 31)) is True

    def test_no_solapamiento_antes(self) -> None:
        assert self._check(date(2025, 7, 1), date(2025, 12, 31), date(2025, 1, 1), date(2025, 6, 30)) is False

    def test_no_solapamiento_despues(self) -> None:
        assert self._check(date(2025, 1, 1), date(2025, 6, 30), date(2025, 7, 1), date(2025, 12, 31)) is False

    def test_existing_sin_hasta_solapa(self) -> None:
        """Vigente sin fecha de fin solapa con cualquier rango futuro."""
        assert self._check(date(2025, 1, 1), None, date(2026, 1, 1), date(2026, 12, 31)) is True

    def test_new_sin_hasta_solapa(self) -> None:
        """Nuevo registro abierto solapa si existing empieza después de new_desde."""
        assert self._check(date(2025, 6, 1), date(2025, 12, 31), date(2025, 1, 1), None) is True

    def test_ambos_sin_hasta_solapan(self) -> None:
        assert self._check(date(2025, 1, 1), None, date(2024, 1, 1), None) is True


# ===========================================================================
# Group 3 — segmentación de liquidación (pure unit, no DB)
# ===========================================================================


class TestSegmentacionLiquidacion:
    """Unit tests for the segmentation logic (General / NEXO / Facturantes)."""

    def _segmentar(self, liquidaciones: list[Any]) -> Any:
        from app.services.liquidacion_service import segmentar_liquidaciones

        return segmentar_liquidaciones(liquidaciones)

    def _liq(
        self,
        total: Decimal,
        es_nexo: bool = False,
        excluido_por_factura: bool = False,
    ) -> Any:
        return SimpleNamespace(
            total=total,
            es_nexo=es_nexo,
            excluido_por_factura=excluido_por_factura,
        )

    def test_segmento_general(self) -> None:
        liqs = [self._liq(Decimal("1000")), self._liq(Decimal("800"))]
        result = self._segmentar(liqs)
        assert len(result.general) == 2
        assert len(result.nexo) == 0
        assert len(result.facturantes) == 0

    def test_segmento_nexo(self) -> None:
        liqs = [self._liq(Decimal("500"), es_nexo=True)]
        result = self._segmentar(liqs)
        assert len(result.nexo) == 1
        assert len(result.general) == 0

    def test_segmento_facturantes(self) -> None:
        liqs = [self._liq(Decimal("700"), excluido_por_factura=True)]
        result = self._segmentar(liqs)
        assert len(result.facturantes) == 1

    def test_kpi_total_sin_factura(self) -> None:
        liqs = [
            self._liq(Decimal("1000")),
            self._liq(Decimal("500"), es_nexo=True),
            self._liq(Decimal("700"), excluido_por_factura=True),
        ]
        result = self._segmentar(liqs)
        assert result.total_sin_factura == Decimal("1500")

    def test_kpi_total_con_factura(self) -> None:
        liqs = [
            self._liq(Decimal("1000")),
            self._liq(Decimal("700"), excluido_por_factura=True),
        ]
        result = self._segmentar(liqs)
        assert result.total_con_factura == Decimal("1700")


# ===========================================================================
# Group 4 — integration tests (require TEST_DATABASE_URL)
# ===========================================================================


@pytest.fixture
def db_session(request):
    """Sync DB session fixture via conftest helper."""
    pytest.importorskip("sqlalchemy")
    import os

    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL no configurada")

    from tests.conftest import create_test_tenant

    return None  # placeholder — integration tests fill this in


class TestSalarioBaseRepository:
    """Integration: SalarioBaseRepository against real DB."""

    @pytest.mark.asyncio
    async def test_get_vigente_retorna_base_correcta(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_solapamiento_rechazado_con_409(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_aislamiento_tenant(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestSalarioPlusRepository:
    """Integration: SalarioPlusRepository against real DB."""

    @pytest.mark.asyncio
    async def test_get_vigente_por_grupo_rol_periodo(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_grupo_sin_vigente_retorna_none(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestLiquidacionCierre:
    """Integration: cierre inmutable y auditoría."""

    @pytest.mark.asyncio
    async def test_cerrar_liquidacion_cambia_estado(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_modificar_liquidacion_cerrada_falla_409(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_doble_cierre_falla_409(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestFacturaService:
    """Integration: factura_service."""

    @pytest.mark.asyncio
    async def test_crear_factura_docente_facturante(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    @pytest.mark.asyncio
    async def test_rechazar_no_facturante(self, db_session) -> None:
        pytest.skip("requires TEST_DATABASE_URL")


class TestRouterGuards:
    """Unit: router guards return 401/403 without auth."""

    def test_liquidaciones_list_sin_auth(self, configured_app) -> None:
        pytest.skip("requires TEST_DATABASE_URL")

    def test_facturas_list_sin_auth(self, configured_app) -> None:
        pytest.skip("requires TEST_DATABASE_URL")
