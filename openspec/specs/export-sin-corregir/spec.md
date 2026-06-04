## ADDED Requirements

### Requirement: Export includes only ungraded textual activities
`GET /api/v1/analisis/export/sin-corregir` SHALL return a downloadable CSV listing student × activity pairs where: the activity is textual (not numeric), the student has a completion record (from the finalizacion import), and no `nota_textual` has been recorded yet (RN-07, RN-08).

#### Scenario: CSV contains correct pending entries
- **WHEN** student A completed textual activity TP1 but has no `nota_textual` for it
- **THEN** the CSV contains a row with student A and TP1

#### Scenario: Numeric activities are excluded from CSV
- **WHEN** student A has no grade for a numeric activity (identified by `(Real)` suffix)
- **THEN** that pair does NOT appear in the CSV export (RN-08)

#### Scenario: Already-graded textual activity not in CSV
- **WHEN** student B completed TP1 and already has `nota_textual` recorded
- **THEN** student B × TP1 does NOT appear in the export

### Requirement: Export endpoint requires atrasados:ver permission
The export endpoint SHALL enforce `atrasados:ver` permission.

#### Scenario: User without permission gets 403
- **WHEN** a user without `atrasados:ver` calls the export endpoint
- **THEN** the system returns `403`

### Requirement: CSV response has correct content-type and filename
The response SHALL have `Content-Type: text/csv` and `Content-Disposition: attachment; filename="sin_corregir_<materia_id>.csv"`.

#### Scenario: Response headers are set correctly
- **WHEN** the export endpoint is called successfully
- **THEN** response headers include `Content-Type: text/csv` and an attachment disposition
