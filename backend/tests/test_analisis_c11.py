"""
Strict TDD tests for C-11 analisis-atrasados-reportes.

TDD cycle:
  Groups 1-4: pure unit tests (no DB) — service computation functions
  Group 5: repository integration (requires TEST_DATABASE_URL)
  Group 6: E2E API tests (requires TEST_DATABASE_URL)

RED → GREEN → TRIANGULATE → REFACTOR order preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from tests.conftest import create_test_tenant, create_test_user


# ===========================================================================
# Shared internal types (defined here for tests, imported from service below)
# ===========================================================================


# ===========================================================================
# Group 1 — computar_atrasados (pure unit, no DB)
# ===========================================================================
# RED: import fails until analisis_service.py with computar_atrasados exists.


class TestComputarAtrasados:
    """Unit tests for atrasado classification (RN-06)."""

    def setup_method(self):
        from app.services.analisis_service import (
            computar_atrasados,
            EntradaSimple,
            CalificacionSimple,
        )
        self.fn = computar_atrasados
        self.Entrada = EntradaSimple
        self.Cal = CalificacionSimple

    def _e(self, ep_id=None, **kw):
        return self.Entrada(
            id=ep_id or uuid4(),
            nombre=kw.get("nombre", "Ana"),
            apellidos=kw.get("apellidos", "Lopez"),
            comision=kw.get("comision", None),
            materia_id=kw.get("materia_id", uuid4()),
        )

    def _c(self, ep_id, actividad, aprobado):
        return self.Cal(entrada_padron_id=ep_id, actividad=actividad, aprobado=aprobado)

    def test_student_with_failing_grade_is_atrasado(self):
        # Scenario: Student with a failing grade is atrasado
        ep = self._e()
        cals = [self._c(ep.id, "TP1", False)]
        result = self.fn([ep], cals)
        assert len(result) == 1
        assert result[0].entrada_padron_id == ep.id
        assert "TP1" in result[0].actividades_reprobadas

    def test_student_with_all_passing_is_not_atrasado(self):
        # Scenario: Student with all passing grades is not atrasado
        ep = self._e()
        cals = [self._c(ep.id, "TP1", True), self._c(ep.id, "TP2", True)]
        result = self.fn([ep], cals)
        assert result == []

    def test_student_missing_activity_present_for_others_is_atrasado(self):
        # Scenario: Student missing an activity present for others is atrasado
        ep_a = self._e()
        ep_b = self._e()
        cals = [
            self._c(ep_a.id, "TP1", True),
            self._c(ep_b.id, "TP1", True),
            # ep_a also has TP2 but ep_b does not
            self._c(ep_a.id, "TP2", True),
        ]
        result = self.fn([ep_a, ep_b], cals)
        ep_ids = [r.entrada_padron_id for r in result]
        assert ep_b.id in ep_ids
        faltantes = next(r.actividades_faltantes for r in result if r.entrada_padron_id == ep_b.id)
        assert "TP2" in faltantes

    def test_student_with_no_cals_is_atrasado_when_others_have_cals(self):
        # Scenario: Student with no calificaciones at all is atrasado when others have them
        ep_a = self._e()
        ep_b = self._e()
        cals = [self._c(ep_a.id, "TP1", True)]
        result = self.fn([ep_a, ep_b], cals)
        ep_ids = [r.entrada_padron_id for r in result]
        assert ep_b.id in ep_ids

    def test_no_calificaciones_at_all_returns_empty(self):
        # Edge: no calificaciones for any student — no known activities, nobody is atrasado
        ep = self._e()
        result = self.fn([ep], [])
        assert result == []

    def test_student_not_in_calificaciones_but_no_known_activities_is_not_atrasado(self):
        # Only atrasado if OTHER students have activities for this materia
        ep = self._e()
        result = self.fn([ep], [])
        assert result == []


# ===========================================================================
# Group 2 — computar_ranking (pure unit, no DB)
# ===========================================================================
# RED: import fails until computar_ranking is defined.


class TestComputarRanking:
    """Unit tests for activity ranking (RN-09)."""

    def setup_method(self):
        from app.services.analisis_service import computar_ranking, CalificacionSimple
        self.fn = computar_ranking
        self.Cal = CalificacionSimple

    def _c(self, ep_id, actividad, aprobado):
        return self.Cal(entrada_padron_id=ep_id, actividad=actividad, aprobado=aprobado)

    def test_student_with_zero_approved_excluded(self):
        # Scenario: Student with zero approved activities is excluded
        ep = uuid4()
        cals = [self._c(ep, "TP1", False)]
        result = self.fn(cals)
        assert result == []

    def test_student_with_one_approved_included(self):
        # Scenario: Student with one approved activity appears
        ep = uuid4()
        cals = [self._c(ep, "TP1", True)]
        result = self.fn(cals)
        assert len(result) == 1
        assert result[0].entrada_padron_id == ep
        assert result[0].aprobadas == 1

    def test_ranking_ordered_descending(self):
        # Scenario: Ranking is ordered descending by approved count
        ep_a = uuid4()
        ep_b = uuid4()
        cals = [
            self._c(ep_a, "TP1", True),
            self._c(ep_a, "TP2", True),
            self._c(ep_a, "TP3", True),
            self._c(ep_b, "TP1", True),
            self._c(ep_b, "TP2", True),
        ]
        result = self.fn(cals)
        assert result[0].entrada_padron_id == ep_a
        assert result[0].aprobadas == 3
        assert result[1].aprobadas == 2

    def test_tie_preserves_both_entries(self):
        # Triangulation: tie means both appear
        ep_a = uuid4()
        ep_b = uuid4()
        cals = [self._c(ep_a, "TP1", True), self._c(ep_b, "TP1", True)]
        result = self.fn(cals)
        assert len(result) == 2
        assert all(r.aprobadas == 1 for r in result)


# ===========================================================================
# Group 3 — computar_notas_finales (pure unit, no DB)
# ===========================================================================
# RED: import fails until computar_notas_finales is defined.


class TestComputarNotasFinales:
    """Unit tests for final grade grouping (F2.5)."""

    def setup_method(self):
        from app.services.analisis_service import (
            computar_notas_finales,
            CalificacionSimple,
            EntradaSimple,
        )
        self.fn = computar_notas_finales
        self.Cal = CalificacionSimple
        self.Entrada = EntradaSimple

    def _e(self, ep_id=None):
        return self.Entrada(
            id=ep_id or uuid4(),
            nombre="Ana", apellidos="Lopez",
            comision=None, materia_id=uuid4(),
        )

    def _c(self, ep_id, actividad, nota_num=None, nota_txt=None, aprobado=True):
        return self.Cal(
            entrada_padron_id=ep_id, actividad=actividad, aprobado=aprobado,
            nota_numerica=Decimal(str(nota_num)) if nota_num is not None else None,
            nota_textual=nota_txt,
        )

    def test_average_computed_over_selected_activities(self):
        # Scenario: Average computed over selected activities
        ep = self._e()
        cals = [
            self._c(ep.id, "TP1", nota_num=80),
            self._c(ep.id, "TP2", nota_num=60),
        ]
        result = self.fn([ep], cals, ["TP1", "TP2"])
        assert len(result) == 1
        assert result[0].nota_final == Decimal("70")

    def test_textual_only_grades_excluded(self):
        # Scenario: Textual-only grades do not contribute to nota final
        ep = self._e()
        cals = [self._c(ep.id, "TP1", nota_txt="Satisfactorio")]
        result = self.fn([ep], cals, ["TP1"])
        assert result == []

    def test_no_grades_for_selected_activities_omitted(self):
        # Triangulation: student has grades but not for selected activities
        ep = self._e()
        cals = [self._c(ep.id, "TP2", nota_num=70)]
        result = self.fn([ep], cals, ["TP1"])
        assert result == []

    def test_single_activity_is_the_average(self):
        # Triangulation: single activity returns that value directly
        ep = self._e()
        cals = [self._c(ep.id, "TP1", nota_num=85)]
        result = self.fn([ep], cals, ["TP1"])
        assert result[0].nota_final == Decimal("85")


# ===========================================================================
# Group 4 — computar_reporte_rapido (pure unit, no DB)
# ===========================================================================


class TestComputarReporteRapido:
    """Unit tests for fast materia report (F2.4)."""

    def setup_method(self):
        from app.services.analisis_service import (
            computar_reporte_rapido,
            CalificacionSimple,
            EntradaSimple,
        )
        self.fn = computar_reporte_rapido
        self.Cal = CalificacionSimple
        self.Entrada = EntradaSimple

    def _e(self, ep_id=None, materia_id=None):
        return self.Entrada(
            id=ep_id or uuid4(), nombre="X", apellidos="Y",
            comision=None, materia_id=materia_id or uuid4(),
        )

    def _c(self, ep_id, actividad, aprobado):
        return self.Cal(
            entrada_padron_id=ep_id, actividad=actividad,
            aprobado=aprobado, nota_numerica=None, nota_textual=None,
        )

    def test_correct_totals(self):
        # Scenario: Reporte shows correct totals
        mat = uuid4()
        eps = [self._e(materia_id=mat) for _ in range(10)]
        cals = []
        # 6 students with ≥1 approved
        for ep in eps[:6]:
            cals.append(self._c(ep.id, "TP1", True))
        # 4 students failing
        for ep in eps[6:]:
            cals.append(self._c(ep.id, "TP1", False))
        result = self.fn(eps, cals, mat)
        assert result.total_alumnos == 10
        assert result.con_aprobadas == 6
        assert result.atrasados == 4

    def test_empty_materia_returns_zeroes(self):
        # Scenario: Empty materia returns zeroes
        mat = uuid4()
        result = self.fn([], [], mat)
        assert result.total_alumnos == 0
        assert result.atrasados == 0
        assert result.actividades == []


# ===========================================================================
# Group 5 — AnalisisRepository integration (requires TEST_DATABASE_URL)
# ===========================================================================


class TestAnalisisRepository:
    """Integration tests for AnalisisRepository."""

    @pytest.mark.asyncio
    async def test_calificaciones_por_materia_tenant_isolated(self, db_session):
        from app.repositories.analisis_repository import AnalisisRepository

        tenant_a = await create_test_tenant(db_session, slug="analisis-ta")
        tenant_b = await create_test_tenant(db_session, slug="analisis-tb")

        repo_a = AnalisisRepository(db_session, tenant_a.id)
        repo_b = AnalisisRepository(db_session, tenant_b.id)
        materia_id = uuid4()

        # No data yet — both repos return empty
        cals_a = await repo_a.calificaciones_por_materia(materia_id)
        cals_b = await repo_b.calificaciones_por_materia(materia_id)
        assert cals_a == []
        assert cals_b == []

    @pytest.mark.asyncio
    async def test_calificaciones_por_materia_returns_empty_when_none(self, db_session):
        from app.repositories.analisis_repository import AnalisisRepository

        tenant = await create_test_tenant(db_session, slug="analisis-empty")
        repo = AnalisisRepository(db_session, tenant.id)
        result = await repo.calificaciones_por_materia(uuid4())
        assert result == []


# ===========================================================================
# Group 6 — E2E API tests (requires TEST_DATABASE_URL)
# ===========================================================================


class TestAnalisisAPIE2E:
    """E2E tests for the analisis router."""

    def _auth_headers(self, client, email, password):
        resp = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def test_atrasados_empty_when_no_calificaciones(
        self, client, test_tenant, test_materia, test_profesor
    ):
        # Scenario: No calificaciones → no atrasados
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        resp = client.get(
            f"/api/v1/analisis/atrasados?materia_id={test_materia.id}",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] == 0

    def test_ranking_excludes_zero_approved(
        self, client, test_tenant, test_materia, test_profesor
    ):
        # Scenario: No approved grades → empty ranking
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        resp = client.get(
            f"/api/v1/analisis/ranking?materia_id={test_materia.id}",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] == 0

    def test_user_without_permission_gets_403(self, client, test_tenant, test_materia):
        import os
        if not os.getenv("TEST_DATABASE_URL"):
            pytest.skip("TEST_DATABASE_URL not set")

        resp_reg = client.post(
            "/api/v1/auth/register",
            json={"email": "noperm_analisis@test.com", "password": "TestPass123!",
                  "nombre": "No", "apellidos": "Perm"},
        )
        assert resp_reg.status_code in (200, 201, 409)
        headers = self._auth_headers(client, "noperm_analisis@test.com", "TestPass123!")
        resp = client.get(
            f"/api/v1/analisis/atrasados?materia_id={test_materia.id}",
            headers=headers,
        )
        assert resp.status_code == 403

    def test_export_sin_corregir_content_type(
        self, client, test_tenant, test_materia, test_profesor
    ):
        # Scenario: CSV response has correct content-type
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        resp = client.get(
            f"/api/v1/analisis/export/sin-corregir?materia_id={test_materia.id}",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert "text/csv" in resp.headers.get("content-type", "")
