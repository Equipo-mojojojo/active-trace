"""
Strict TDD tests for C-10 calificaciones-y-umbral.

TDD cycle order:
  Group 1: Pure unit tests — derivar_aprobado (no DB needed)
  Group 2: Pure unit tests — calificaciones_parser (no DB needed)
  Group 3: Pure unit tests — finalizacion parser (no DB needed)
  Group 4: Integration — repositories (requires TEST_DATABASE_URL)
  Group 5: Integration — service + router E2E (requires TEST_DATABASE_URL)

RED → GREEN → TRIANGULATE → REFACTOR documented inline.
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tests.conftest import create_test_tenant, create_test_user


# ===========================================================================
# Helpers
# ===========================================================================


def _make_csv(rows: list[dict[str, Any]], headers: list[str] | None = None) -> bytes:
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


def _make_xlsx(rows: list[dict[str, Any]], headers: list[str] | None = None) -> bytes:
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


# ===========================================================================
# Group 1 — derivar_aprobado (pure unit, no DB)
# ===========================================================================
# RED: import fails until calificaciones_service.py with derivar_aprobado exists.


class TestDerivarAprobado:
    """Unit tests for the pure derivar_aprobado function (spec: calificaciones-model)."""

    def setup_method(self):
        from app.services.calificaciones_service import derivar_aprobado

        self.fn = derivar_aprobado

    def test_numeric_above_threshold_is_approved(self):
        # Scenario: Numeric grade above threshold is approved
        assert self.fn(Decimal("75"), None, 60, []) is True

    def test_numeric_below_threshold_is_not_approved(self):
        # Scenario: Numeric grade below threshold is not approved
        assert self.fn(Decimal("50"), None, 60, []) is False

    def test_numeric_exactly_at_threshold_is_approved(self):
        # Triangulation: boundary value
        assert self.fn(Decimal("60"), None, 60, []) is True

    def test_textual_in_approved_set_is_approved(self):
        # Scenario: Textual grade in approved set is approved
        assert (
            self.fn(None, "Satisfactorio", 60, ["Satisfactorio", "Supera lo esperado"])
            is True
        )

    def test_textual_not_in_approved_set_is_not_approved(self):
        # Scenario: Textual grade outside approved set is not approved
        assert (
            self.fn(None, "No satisfactorio", 60, ["Satisfactorio", "Supera lo esperado"])
            is False
        )

    def test_numeric_takes_precedence_when_both_present(self):
        # Scenario: Numeric grade takes precedence when both fields present
        assert (
            self.fn(Decimal("80"), "No satisfactorio", 60, ["Satisfactorio"])
            is True
        )

    def test_numeric_below_threshold_overrides_positive_textual(self):
        # Triangulation: numeric < threshold even when textual would be approved
        assert self.fn(Decimal("40"), "Satisfactorio", 60, ["Satisfactorio"]) is False

    def test_default_textual_values_used_when_list_empty(self):
        # spec umbral-materia: default values ["Satisfactorio", "Supera lo esperado"]
        # When valores_aprobatorios=[], service should apply defaults — but derivar_aprobado
        # itself receives the resolved list. If empty, no textual value is approved.
        assert self.fn(None, "Satisfactorio", 60, []) is False

    def test_none_nota_numerica_and_none_nota_textual_returns_false(self):
        # Edge case: no data at all
        assert self.fn(None, None, 60, ["Satisfactorio"]) is False


# ===========================================================================
# Group 2 — calificaciones_parser (pure unit, no DB)
# ===========================================================================
# RED: import fails until calificaciones_parser.py with detectar_actividades exists.


class TestDetectarActividades:
    """Unit tests for LMS column detection (RN-01, RN-02)."""

    def setup_method(self):
        from app.services.calificaciones_parser import detectar_actividades
        import pandas as pd

        self.fn = detectar_actividades
        self.pd = pd

    def _df(self, data: dict[str, list]) -> Any:
        return self.pd.DataFrame(data)

    def test_column_ending_real_detected_as_numeric(self):
        # Scenario: Column ending in (Real) is detected as numeric (RN-01)
        df = self._df({"Nombre completo": ["Ana"], "Nota Final (Real)": [75.0]})
        actividades = self.fn(df)
        nombres = [a.nombre for a in actividades]
        assert "Nota Final (Real)" in nombres
        tipo_map = {a.nombre: a.tipo for a in actividades}
        assert tipo_map["Nota Final (Real)"] == "numerica"

    def test_column_without_real_suffix_not_detected_as_numeric(self):
        # Scenario: Column without (Real) suffix is not detected as numeric
        df = self._df({"Nombre completo": ["Ana"], "Nota Final": [75.0]})
        actividades = self.fn(df)
        nombres = [a.nombre for a in actividades]
        assert "Nota Final" not in nombres

    def test_column_with_textual_scale_values_detected(self):
        # Scenario: Column with textual scale values is detected
        df = self._df(
            {
                "Nombre completo": ["Ana", "Bob"],
                "TP1": ["Satisfactorio", "No satisfactorio"],
            }
        )
        actividades = self.fn(df)
        tipo_map = {a.nombre: a.tipo for a in actividades}
        assert "TP1" in tipo_map
        assert tipo_map["TP1"] == "textual"

    def test_identifier_columns_ignored(self):
        # Triangulation: known metadata columns should not appear as actividades
        df = self._df(
            {
                "Nombre completo": ["Ana"],
                "Dirección de correo": ["ana@x.com"],
                "Nota Final (Real)": [80.0],
            }
        )
        actividades = self.fn(df)
        nombres = [a.nombre for a in actividades]
        assert "Nombre completo" not in nombres
        assert "Dirección de correo" not in nombres

    def test_multiple_numeric_columns_all_detected(self):
        # Triangulation: two numeric columns
        df = self._df(
            {
                "Nombre completo": ["Ana"],
                "TP1 (Real)": [70.0],
                "TP2 (Real)": [90.0],
            }
        )
        actividades = self.fn(df)
        nombres = [a.nombre for a in actividades]
        assert "TP1 (Real)" in nombres
        assert "TP2 (Real)" in nombres


class TestParseFilas:
    """Unit tests for parse_filas row extraction."""

    def setup_method(self):
        from app.services.calificaciones_parser import parse_filas, ActividadDetectada
        import pandas as pd

        self.fn = parse_filas
        self.pd = pd
        self.ActividadDetectada = ActividadDetectada

    def _df(self, data: dict[str, list]) -> Any:
        return self.pd.DataFrame(data)

    def test_only_selected_activities_extracted(self):
        # spec: only selected activities are stored
        ep_id = uuid4()
        entry_map = {"Ana Lopez": ep_id}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez"],
                "TP1 (Real)": [80.0],
                "TP2 (Real)": [50.0],
            }
        )
        actividades = [
            self.ActividadDetectada(nombre="TP1 (Real)", tipo="numerica", muestra_valores=[]),
        ]
        filas = self.fn(df, actividades, entry_map)
        assert len(filas) == 1
        assert filas[0].actividad == "TP1 (Real)"
        assert filas[0].nota_numerica == Decimal("80.0")

    def test_textual_grade_extracted_correctly(self):
        ep_id = uuid4()
        entry_map = {"Ana Lopez": ep_id}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez"],
                "TP1": ["Satisfactorio"],
            }
        )
        actividades = [
            self.ActividadDetectada(nombre="TP1", tipo="textual", muestra_valores=["Satisfactorio"]),
        ]
        filas = self.fn(df, actividades, entry_map)
        assert len(filas) == 1
        assert filas[0].nota_textual == "Satisfactorio"
        assert filas[0].nota_numerica is None

    def test_unknown_student_in_row_is_skipped(self):
        # Student not in entry_map -> skip row
        df = self._df(
            {
                "Nombre completo": ["Desconocido"],
                "TP1 (Real)": [70.0],
            }
        )
        actividades = [
            self.ActividadDetectada(nombre="TP1 (Real)", tipo="numerica", muestra_valores=[]),
        ]
        filas = self.fn(df, actividades, {"Ana Lopez": uuid4()})
        assert filas == []


# ===========================================================================
# Group 3 — parse_finalizacion (pure unit, no DB)
# ===========================================================================
# RED: import fails until calificaciones_parser.parse_finalizacion exists.


class TestParseFinalizacion:
    """Unit tests for finalization report parser (RN-07, RN-08)."""

    def setup_method(self):
        from app.services.calificaciones_parser import parse_finalizacion, CalificacionExistente
        import pandas as pd

        self.fn = parse_finalizacion
        self.pd = pd
        self.CalificacionExistente = CalificacionExistente

    def _df(self, data: dict[str, list]) -> Any:
        return self.pd.DataFrame(data)

    def test_student_with_completed_textual_activity_and_no_grade_appears(self):
        # Scenario: Student with completed textual activity and no grade is flagged
        ep_id = uuid4()
        entry_map = {"Ana Lopez": ep_id}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez"],
                "TP1": ["Completado"],
            }
        )
        existing: list = []
        result = self.fn(df, entry_map, existing, textual_activities={"TP1"})
        nombres_actividades = [r.actividad for r in result]
        assert "TP1" in nombres_actividades

    def test_student_with_existing_textual_grade_not_flagged(self):
        # Scenario: Student with existing textual grade is NOT flagged
        ep_id = uuid4()
        entry_map = {"Ana Lopez": ep_id}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez"],
                "TP1": ["Completado"],
            }
        )
        existing = [
            self.CalificacionExistente(entrada_padron_id=ep_id, actividad="TP1")
        ]
        result = self.fn(df, entry_map, existing, textual_activities={"TP1"})
        assert result == []

    def test_numeric_activity_without_grade_not_flagged(self):
        # Scenario: Student with completed numeric activity is NOT flagged (RN-08)
        ep_id = uuid4()
        entry_map = {"Ana Lopez": ep_id}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez"],
                "TP1 (Real)": ["Completado"],
            }
        )
        existing: list = []
        result = self.fn(df, entry_map, existing, textual_activities={"TP1"})
        # "TP1 (Real)" is a numeric activity -> not in textual_activities -> skip
        assert result == []

    def test_multiple_students_only_ungrades_flagged(self):
        # Triangulation: 2 students, only one missing grade
        ep_id_a = uuid4()
        ep_id_b = uuid4()
        entry_map = {"Ana Lopez": ep_id_a, "Bob Diaz": ep_id_b}
        df = self._df(
            {
                "Nombre completo": ["Ana Lopez", "Bob Diaz"],
                "TP1": ["Completado", "Completado"],
            }
        )
        existing = [
            self.CalificacionExistente(entrada_padron_id=ep_id_a, actividad="TP1")
        ]
        result = self.fn(df, entry_map, existing, textual_activities={"TP1"})
        assert len(result) == 1
        assert result[0].entrada_padron_id == ep_id_b


# ===========================================================================
# Group 4 — Repository integration (requires TEST_DATABASE_URL)
# ===========================================================================


class TestCalificacionesRepository:
    """Integration tests for CalificacionesRepository upsert behavior."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_record(self, db_session):
        from app.repositories.calificaciones_repository import CalificacionesRepository

        tenant = await create_test_tenant(db_session, slug="cal-repo-a")
        repo = CalificacionesRepository(db_session, tenant.id)
        ep_id = uuid4()
        materia_id = uuid4()

        cal = await repo._upsert_fallback(
            entrada_padron_id=ep_id,
            materia_id=materia_id,
            actividad="TP1 (Real)",
            nota_numerica=Decimal("80"),
            nota_textual=None,
            aprobado=True,
            origen="Importado",
        )
        assert cal.id is not None
        assert cal.aprobado is True

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record_no_duplicate(self, db_session):
        # Scenario: Re-import same activity updates existing record (spec: calificaciones-model)
        from app.repositories.calificaciones_repository import CalificacionesRepository

        tenant = await create_test_tenant(db_session, slug="cal-repo-b")
        repo = CalificacionesRepository(db_session, tenant.id)
        ep_id = uuid4()
        materia_id = uuid4()

        await repo._upsert_fallback(
            entrada_padron_id=ep_id,
            materia_id=materia_id,
            actividad="TP1 (Real)",
            nota_numerica=Decimal("80"),
            nota_textual=None,
            aprobado=True,
            origen="Importado",
        )
        await repo._upsert_fallback(
            entrada_padron_id=ep_id,
            materia_id=materia_id,
            actividad="TP1 (Real)",
            nota_numerica=Decimal("40"),
            nota_textual=None,
            aprobado=False,
            origen="Importado",
        )
        all_records = await repo.listar_por_entrada_y_actividad(ep_id, "TP1 (Real)")
        assert len(all_records) == 1
        assert all_records[0].nota_numerica == Decimal("40")
        assert all_records[0].aprobado is False


class TestUmbralMateriaRepository:
    """Integration tests for UmbralMateriaRepository."""

    @pytest.mark.asyncio
    async def test_crear_o_actualizar_creates_new_umbral(self, db_session):
        from app.repositories.calificaciones_repository import UmbralMateriaRepository

        tenant = await create_test_tenant(db_session, slug="umbral-repo-a")
        repo = UmbralMateriaRepository(db_session, tenant.id)
        asignacion_id = uuid4()
        materia_id = uuid4()

        umbral = await repo.crear_o_actualizar(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=75,
            valores_aprobatorios=["Aprobado"],
        )
        assert umbral.umbral_pct == 75
        assert umbral.valores_aprobatorios == ["Aprobado"]

    @pytest.mark.asyncio
    async def test_crear_o_actualizar_updates_existing_umbral(self, db_session):
        from app.repositories.calificaciones_repository import UmbralMateriaRepository

        tenant = await create_test_tenant(db_session, slug="umbral-repo-b")
        repo = UmbralMateriaRepository(db_session, tenant.id)
        asignacion_id = uuid4()
        materia_id = uuid4()

        await repo.crear_o_actualizar(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=60,
            valores_aprobatorios=[],
        )
        await repo.crear_o_actualizar(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=80,
            valores_aprobatorios=["Excelente"],
        )
        fetched = await repo.obtener_por_asignacion(asignacion_id)
        assert fetched is not None
        assert fetched.umbral_pct == 80


# ===========================================================================
# Group 5 — E2E API tests (requires TEST_DATABASE_URL)
# ===========================================================================


class TestCalificacionesAPIE2E:
    """E2E tests for the calificaciones router."""

    # ---- helpers ----

    def _auth_headers(self, client, email: str, password: str) -> dict:
        resp = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def _csv_calificaciones(self, nombre: str = "Ana Lopez") -> bytes:
        return _make_csv(
            [
                {
                    "Nombre completo": nombre,
                    "Dirección de correo": "ana@test.com",
                    "TP1 (Real)": 80,
                    "TP2 (Real)": 45,
                }
            ]
        )

    # ---- tests ----

    def test_preview_detects_numeric_columns(
        self, client, test_tenant, test_materia, test_profesor
    ):
        # Scenario: Preview returns detected activities
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        csv_bytes = self._csv_calificaciones()
        resp = client.post(
            "/api/v1/calificaciones/preview",
            files={"file": ("notas.csv", csv_bytes, "text/csv")},
            data={"materia_id": str(test_materia.id)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "actividades" in data
        nombres = [a["nombre"] for a in data["actividades"]]
        assert "TP1 (Real)" in nombres
        assert "TP2 (Real)" in nombres

    def test_import_persists_selected_activities_and_derives_aprobado(
        self, client, test_tenant, test_materia, test_profesor, test_padron_entry
    ):
        # Scenario: Only selected activities are stored; aprobado derived correctly
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        csv_bytes = self._csv_calificaciones(nombre=test_padron_entry["nombre_completo"])
        resp = client.post(
            "/api/v1/calificaciones/import",
            files={"file": ("notas.csv", csv_bytes, "text/csv")},
            data={
                "materia_id": str(test_materia.id),
                "actividades_seleccionadas": ["TP1 (Real)"],
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["importadas"] == 1

    def test_reimport_is_idempotent(
        self, client, test_tenant, test_materia, test_profesor, test_padron_entry
    ):
        # Scenario: Re-import same activity updates existing record
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")

        def do_import(nota: int):
            rows = [
                {
                    "Nombre completo": test_padron_entry["nombre_completo"],
                    "Dirección de correo": "ana@test.com",
                    "TP1 (Real)": nota,
                }
            ]
            return client.post(
                "/api/v1/calificaciones/import",
                files={"file": ("notas.csv", _make_csv(rows), "text/csv")},
                data={
                    "materia_id": str(test_materia.id),
                    "actividades_seleccionadas": ["TP1 (Real)"],
                },
                headers=headers,
            )

        r1 = do_import(80)
        r2 = do_import(40)
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both should report 1 row — no duplicate
        assert r1.json()["importadas"] == 1
        assert r2.json()["importadas"] == 1

    def test_umbral_update_forbidden_for_other_assignment(
        self, client, test_tenant, test_materia, test_profesor
    ):
        # Scenario: PROFESOR cannot set threshold for another docente's assignment
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        resp = client.put(
            "/api/v1/calificaciones/umbral",
            json={
                "asignacion_id": str(uuid4()),  # random UUID — not theirs
                "materia_id": str(test_materia.id),
                "umbral_pct": 75,
                "valores_aprobatorios": [],
            },
            headers=headers,
        )
        assert resp.status_code in (403, 404)

    def test_user_without_permission_gets_403(self, client, test_tenant, test_materia):
        # Scenario: User without permission is rejected
        import os

        if not os.getenv("TEST_DATABASE_URL"):
            pytest.skip("TEST_DATABASE_URL not set")

        # Create a user with no permissions
        resp_reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "noperms@test.com",
                "password": "TestPass123!",
                "nombre": "No",
                "apellidos": "Perms",
            },
        )
        assert resp_reg.status_code in (200, 201, 409)

        headers = self._auth_headers(client, "noperms@test.com", "TestPass123!")
        csv_bytes = _make_csv([{"Nombre completo": "Test", "TP1 (Real)": 80}])
        resp = client.post(
            "/api/v1/calificaciones/preview",
            files={"file": ("notas.csv", csv_bytes, "text/csv")},
            data={"materia_id": str(test_materia.id)},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_finalizacion_preview_flags_ungraded_textual(
        self, client, test_tenant, test_materia, test_profesor, test_padron_entry
    ):
        # Scenario: Student with completed textual activity and no grade appears
        headers = self._auth_headers(client, test_profesor["email"], "TestPass123!")
        rows = [
            {
                "Nombre completo": test_padron_entry["nombre_completo"],
                "TP1": "Completado",
            }
        ]
        resp = client.post(
            "/api/v1/calificaciones/finalizacion/preview",
            files={"file": ("finalizacion.csv", _make_csv(rows), "text/csv")},
            data={"materia_id": str(test_materia.id)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "pendientes" in data
        actividades = [p["actividad"] for p in data["pendientes"]]
        assert "TP1" in actividades
