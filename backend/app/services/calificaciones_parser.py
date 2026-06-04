"""
CalificacionesParser: Parse LMS grade export files (xlsx/csv).

Design decisions applied:
  D5: Numeric columns detected by (Real) suffix (RN-01).
  D6: Textual columns detected by value set match (RN-02).
  D4: Parse only; no persistence logic here.

Exported symbols:
  detectar_actividades(df) -> list[ActividadDetectada]
  parse_filas(df, actividades, entry_map) -> list[CalificacionRaw]
  parse_finalizacion(df, entry_map, existing, textual_activities) -> list[EntradaPendienteCorreccion]
  parse_calificaciones_file(file_bytes, filename) -> pd.DataFrame
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

# LMS metadata columns — never treated as grade activities
_METADATA_COLUMNS = frozenset(
    {
        "nombre completo",
        "dirección de correo",
        "direccion de correo",
        "email",
        "correo",
        "id",
        "departamento",
        "grupo",
        "comisión",
        "comision",
    }
)

# Textual scale values (RN-02) — used to auto-detect textual columns
TEXTUAL_SCALE_VALUES = frozenset(
    {
        "satisfactorio",
        "supera lo esperado",
        "no satisfactorio",
        "no alcanzado",
        "en proceso",
        "aprobado",
        "desaprobado",
        "completado",
        "no completado",
        "no entregado",
        "pendiente",
    }
)

# Column that stores the student full name in LMS exports
_NAME_COLUMN_ALIASES = {"nombre completo", "full name", "nombre", "student"}


class CalificacionesParseError(ValueError):
    """Raised when the file cannot be parsed."""


@dataclass
class ActividadDetectada:
    nombre: str
    tipo: str  # "numerica" | "textual"
    muestra_valores: list[str] = field(default_factory=list)


@dataclass
class CalificacionRaw:
    entrada_padron_id: UUID
    actividad: str
    nota_numerica: Decimal | None
    nota_textual: str | None


@dataclass
class CalificacionExistente:
    entrada_padron_id: UUID
    actividad: str


@dataclass
class EntradaPendienteCorreccion:
    entrada_padron_id: UUID
    actividad: str


# Type alias — kept for import compatibility with tests
PadronMapEntry = dict[str, UUID]


def parse_calificaciones_file(file_bytes: bytes, filename: str) -> Any:
    """Load an LMS grade file into a pandas DataFrame.

    Supports .xlsx and .csv. Raises CalificacionesParseError on unsupported
    formats or parse failures.
    """
    import pandas as pd

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    try:
        if ext == "xlsx":
            return pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        elif ext == "csv":
            return pd.read_csv(io.StringIO(file_bytes.decode("utf-8", errors="replace")))
        else:
            raise CalificacionesParseError(f"Unsupported file format: .{ext}")
    except CalificacionesParseError:
        raise
    except Exception as exc:
        raise CalificacionesParseError(f"Could not parse file: {exc}") from exc


def _find_name_column(columns: list[str]) -> str | None:
    """Return the column that holds the student full name, or None."""
    for col in columns:
        if col.strip().lower() in _NAME_COLUMN_ALIASES:
            return col
    return None


def detectar_actividades(df: Any) -> list[ActividadDetectada]:
    """Classify DataFrame columns as numeric or textual grade activities (RN-01, RN-02).

    Numeric: column name ends with '(Real)' (case-insensitive).
    Textual: column values overlap with TEXTUAL_SCALE_VALUES.
    Metadata columns (name, email, etc.) are always excluded.
    """
    actividades: list[ActividadDetectada] = []

    for col in df.columns:
        col_lower = col.strip().lower()
        if col_lower in _METADATA_COLUMNS:
            continue

        # RN-01: numeric detection by suffix
        if col_lower.endswith("(real)"):
            actividades.append(
                ActividadDetectada(nombre=col, tipo="numerica", muestra_valores=[])
            )
            continue

        # RN-02: textual detection by value set intersection
        col_values = {
            str(v).strip().lower()
            for v in df[col].dropna().unique()
            if str(v).strip()
        }
        if col_values & TEXTUAL_SCALE_VALUES:
            sample = [
                str(v).strip()
                for v in df[col].dropna().unique()
                if str(v).strip().lower() in TEXTUAL_SCALE_VALUES
            ][:5]
            actividades.append(
                ActividadDetectada(nombre=col, tipo="textual", muestra_valores=sample)
            )

    return actividades


def parse_filas(
    df: Any,
    actividades_seleccionadas: list[ActividadDetectada],
    entry_map: dict[str, UUID],
) -> list[CalificacionRaw]:
    """Extract CalificacionRaw records for selected activities.

    entry_map: {nombre_completo -> entrada_padron_id}
    Rows whose nombre_completo is not in entry_map are silently skipped.
    """
    name_col = _find_name_column(list(df.columns))
    if name_col is None:
        return []

    actividad_set = {a.nombre: a for a in actividades_seleccionadas}
    filas: list[CalificacionRaw] = []

    for _, row in df.iterrows():
        nombre_completo = str(row.get(name_col, "")).strip()
        ep_id = entry_map.get(nombre_completo)
        if ep_id is None:
            continue

        for act_name, act in actividad_set.items():
            raw_val = row.get(act_name)
            if raw_val is None or (isinstance(raw_val, float) and __import__("math").isnan(raw_val)):
                continue

            if act.tipo == "numerica":
                try:
                    nota_num = Decimal(str(raw_val))
                    nota_txt = None
                except InvalidOperation:
                    continue
            else:
                nota_num = None
                nota_txt = str(raw_val).strip() if str(raw_val).strip() else None
                if nota_txt is None:
                    continue

            filas.append(
                CalificacionRaw(
                    entrada_padron_id=ep_id,
                    actividad=act_name,
                    nota_numerica=nota_num,
                    nota_textual=nota_txt,
                )
            )

    return filas


def parse_finalizacion(
    df: Any,
    entry_map: dict[str, UUID],
    existing: list[CalificacionExistente],
    textual_activities: set[str],
) -> list[EntradaPendienteCorreccion]:
    """Cross-reference completion report with existing grades (RN-07, RN-08).

    Returns entries where a student has completed a TEXTUAL activity but
    has no nota_textual recorded yet.

    Numeric activities (containing '(Real)') are excluded (RN-08).
    """
    name_col = _find_name_column(list(df.columns))
    if name_col is None:
        return []

    graded_set = {(str(e.entrada_padron_id), e.actividad) for e in existing}

    pendientes: list[EntradaPendienteCorreccion] = []

    # Activity columns in the completion report = columns that are not metadata
    activity_cols = [
        col for col in df.columns
        if col.strip().lower() not in _METADATA_COLUMNS
        and col != name_col
    ]

    for _, row in df.iterrows():
        nombre_completo = str(row.get(name_col, "")).strip()
        ep_id = entry_map.get(nombre_completo)
        if ep_id is None:
            continue

        for col in activity_cols:
            # RN-08: skip numeric activities
            if col.strip().lower().endswith("(real)"):
                continue
            # Only check activities known to be textual (from grade import context)
            if col not in textual_activities:
                continue

            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ("", "nan", "no completado", "no iniciado"):
                continue  # not completed

            key = (str(ep_id), col)
            if key not in graded_set:
                pendientes.append(
                    EntradaPendienteCorreccion(entrada_padron_id=ep_id, actividad=col)
                )

    return pendientes
