## ADDED Requirements

### Requirement: Parser detects numeric columns by (Real) suffix
The LMS export parser SHALL classify a column as a numeric grade column if and only if its header ends with `(Real)` (case-insensitive). All other columns SHALL be ignored for numeric grading.

#### Scenario: Column ending in (Real) is detected as numeric
- **WHEN** the uploaded file contains a column named `"Nota Final (Real)"`
- **THEN** it appears in the preview as a detectable numeric activity

#### Scenario: Column without (Real) suffix is not detected as numeric
- **WHEN** the uploaded file contains a column named `"Nota Final"`
- **THEN** it does NOT appear in the preview as a numeric activity

### Requirement: Parser detects textual columns by known value set
The parser SHALL classify a column as a textual grade column if its cell values match entries from a known textual scale (e.g., "Satisfactorio", "Supera lo esperado", "No satisfactorio"). The known scale SHALL be a system-level configuration.

#### Scenario: Column with textual scale values is detected
- **WHEN** a column contains values like "Satisfactorio" or "No satisfactorio"
- **THEN** it appears in the preview as a detectable textual activity

### Requirement: Import exposes a preview endpoint before persisting
The system SHALL provide `POST /api/v1/calificaciones/preview` that accepts the LMS file and returns the list of detected activities with their types (numeric/textual) WITHOUT writing any data.

#### Scenario: Preview returns detected activities
- **WHEN** a valid LMS file is uploaded to `/preview`
- **THEN** the response contains a list of activities with `{nombre, tipo, muestra_valores}` and no data is persisted

#### Scenario: Preview with invalid file format returns 422
- **WHEN** a file with unsupported format is uploaded to `/preview`
- **THEN** the system returns `422 Unprocessable Entity`

### Requirement: Import persists selected activities only
`POST /api/v1/calificaciones/import` SHALL accept the file plus a list of selected activity names. Only the selected activities SHALL be persisted. Non-selected activities SHALL be ignored.

#### Scenario: Only selected activities are stored
- **WHEN** a file with 5 activities is imported and the user selects 3
- **THEN** only `Calificacion` rows for the 3 selected activities are created or updated; the other 2 produce no rows

### Requirement: Import is idempotent
Re-running import for the same file SHALL upsert existing rows, not duplicate them.

#### Scenario: Re-import updates existing grades
- **WHEN** import is called twice for the same `(entrada_padron_id, actividad)` with different `nota_numerica` values
- **THEN** only one row exists per pair after the second call, reflecting the latest value

### Requirement: Import generates audit event
`POST /api/v1/calificaciones/import` SHALL generate a `CALIFICACIONES_IMPORTAR` audit record on success.

#### Scenario: Successful import creates audit record
- **WHEN** a valid import completes
- **THEN** an audit event `CALIFICACIONES_IMPORTAR` is recorded with `tenant_id`, `usuario_id`, `materia_id`, and count of imported rows

### Requirement: Import requires calificaciones:importar permission
Both `/preview` and `/import` endpoints SHALL require the `calificaciones:importar` permission. PROFESOR has this permission for their own materias; COORDINADOR for any materia in the tenant.

#### Scenario: User without permission is rejected
- **WHEN** a user without `calificaciones:importar` permission calls the import endpoint
- **THEN** the system returns `403`

### Requirement: Importación y preview resuelven alumnos contra el padrón versionado válido
Los flujos `POST /api/v1/calificaciones/preview` y `POST /api/v1/calificaciones/import` SHALL resolver alumnos usando el padrón versionado válido del tenant para la materia solicitada, siguiendo el vínculo `VersionPadron` → `EntradaPadron` y sin depender de columnas académicas inexistentes en `EntradaPadron`.

#### Scenario: Importación usa entradas del padrón activo real
- **WHEN** existe una versión activa de padrón válida para la materia en el contexto solicitado
- **THEN** el import cruza alumnos exclusivamente contra las `EntradaPadron` pertenecientes a esa versión válida

#### Scenario: El import no asume `materia_id` directo en EntradaPadron
- **WHEN** el service resuelve alumnos para importar calificaciones
- **THEN** la implementación obtiene el contexto académico a través de `VersionPadron` y no leyendo un campo inexistente en `EntradaPadron`

#### Scenario: Padrón no correspondiente no participa del cruce
- **WHEN** existen entradas históricas o de otra versión/corte académico del mismo tenant
- **THEN** el import no las usa para mapear alumnos de la corrida actual
