"""
PadronParser: Parse xlsx/csv files into a list of student dicts.

Design D2: Parser is fully decoupled from persistence.
Input: raw file bytes + filename.
Output: list[dict] with keys: nombre, apellidos, email, comision, regional.

Rules:
- Supports .xlsx (openpyxl) and .csv (stdlib csv).
- Column headers are normalised: strip + lowercase.
- 'grupo' is treated as a synonym for 'comision'.
- 'apellido' is treated as a synonym for 'apellidos'.
- Limit: max 5000 data rows — raises PadronParseError if exceeded.
- Unsupported extension: raises PadronParseError.
"""

from __future__ import annotations

import csv
import io
from typing import Any


MAX_ROWS = 5000

# Canonical column names → accepted aliases (all already lowercased/stripped)
_COLUMN_ALIASES: dict[str, list[str]] = {
    "nombre": ["nombre"],
    "apellidos": ["apellidos", "apellido"],
    "email": ["email", "correo", "mail"],
    "comision": ["comision", "grupo", "comisión", "commission"],
    "regional": ["regional", "sede", "region", "región"],
}

# Reverse map: alias → canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in _COLUMN_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias] = _canonical


class PadronParseError(ValueError):
    """Raised when the file cannot be parsed (format, limit, missing columns)."""


def _normalize_header(raw: str) -> str:
    """Strip whitespace and lowercase a header cell."""
    return raw.strip().lower()


def _map_headers(raw_headers: list[str]) -> dict[int, str]:
    """Map column indices to canonical names, ignoring unknown columns."""
    mapping: dict[int, str] = {}
    for idx, raw in enumerate(raw_headers):
        normalised = _normalize_header(raw)
        canonical = _ALIAS_TO_CANONICAL.get(normalised)
        if canonical is not None:
            # Keep the first occurrence of each canonical name
            if canonical not in mapping.values():
                mapping[idx] = canonical
    return mapping


def _row_to_dict(
    row_values: list[Any],
    col_map: dict[int, str],
) -> dict[str, str | None]:
    """Convert a list of cell values to a canonical dict."""
    result: dict[str, str | None] = {
        "nombre": None,
        "apellidos": None,
        "email": None,
        "comision": None,
        "regional": None,
    }
    for idx, canonical in col_map.items():
        if idx < len(row_values):
            raw_val = row_values[idx]
            result[canonical] = str(raw_val).strip() if raw_val is not None and str(raw_val).strip() != "" else None
    return result


def _parse_csv(content: bytes) -> list[dict[str, str | None]]:
    """Parse CSV bytes into a list of canonical dicts."""
    try:
        text = content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return []

    headers = rows[0]
    data_rows = rows[1:]

    if len(data_rows) > MAX_ROWS:
        raise PadronParseError(
            f"El archivo supera el límite de {MAX_ROWS} filas de datos. "
            f"Encontradas: {len(data_rows)}."
        )

    col_map = _map_headers(headers)
    result = []
    for row in data_rows:
        # Skip completely empty rows
        if all(cell.strip() == "" for cell in row):
            continue
        result.append(_row_to_dict(row, col_map))

    return result


def _parse_xlsx(content: bytes) -> list[dict[str, str | None]]:
    """Parse XLSX bytes into a list of canonical dicts."""
    try:
        import openpyxl
    except ImportError as exc:
        raise PadronParseError(
            "La librería openpyxl no está instalada. Instalá con: pip install openpyxl"
        ) from exc

    wb = openpyxl.load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active

    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not all_rows:
        return []

    headers = [str(cell) if cell is not None else "" for cell in all_rows[0]]
    data_rows = all_rows[1:]

    if len(data_rows) > MAX_ROWS:
        raise PadronParseError(
            f"El archivo supera el límite de {MAX_ROWS} filas de datos. "
            f"Encontradas: {len(data_rows)}."
        )

    col_map = _map_headers(headers)
    result = []
    for row in data_rows:
        row_list = list(row)
        # Skip fully-empty rows
        if all(cell is None or str(cell).strip() == "" for cell in row_list):
            continue
        result.append(_row_to_dict(row_list, col_map))

    return result


def parse_padron(file_bytes: bytes, filename: str) -> list[dict[str, str | None]]:
    """Parse a padron file (xlsx or csv) and return a list of student dicts.

    Args:
        file_bytes: Raw file content.
        filename: Original filename (used to determine format by extension).

    Returns:
        list of dicts with canonical keys:
          nombre, apellidos, email, comision, regional.

    Raises:
        PadronParseError: If the file format is unsupported or limits are exceeded.
    """
    lower_name = filename.strip().lower()

    if lower_name.endswith(".csv"):
        return _parse_csv(file_bytes)

    if lower_name.endswith(".xlsx"):
        return _parse_xlsx(file_bytes)

    raise PadronParseError(
        f"Formato de archivo no soportado: '{filename}'. "
        "Solo se aceptan archivos .xlsx y .csv."
    )


def get_detected_columns(rows: list[dict]) -> list[str]:
    """Return the canonical column names that have at least one non-None value."""
    detected: set[str] = set()
    for row in rows:
        for key, val in row.items():
            if val is not None:
                detected.add(key)
    return sorted(detected)
