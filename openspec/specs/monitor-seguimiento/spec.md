## ADDED Requirements

### Requirement: Monitor scope is derived from JWT role
`GET /api/v1/analisis/monitor` SHALL apply different data scopes based on the actor's role (D5):
- TUTOR / PROFESOR: results are limited to students in materias where the actor has an active `Asignacion`.
- COORDINADOR / ADMIN: full tenant access.

#### Scenario: PROFESOR sees only their assigned materias
- **WHEN** a PROFESOR calls the monitor endpoint
- **THEN** only students from materias with an active Asignacion for that PROFESOR are returned

#### Scenario: COORDINADOR sees all materias in the tenant
- **WHEN** a COORDINADOR calls the monitor endpoint
- **THEN** all students in the tenant are included (subject to other filters)

### Requirement: Monitor supports multiple filter parameters
The monitor endpoint SHALL accept optional filters: `materia_id`, `comision`, `regional`, `q` (free text search on student name/email), and `min_aprobadas` (minimum number of approved activities).

#### Scenario: Filter by comision restricts results
- **WHEN** `comision=A1` is provided
- **THEN** only students with `comision=A1` appear in the response

#### Scenario: min_aprobadas filter works correctly
- **WHEN** `min_aprobadas=3` is provided and student A has 2 approved activities
- **THEN** student A does NOT appear in the filtered results

#### Scenario: Free text search matches student email
- **WHEN** `q` matches part of the student's email address within the actor scope
- **THEN** the monitor includes that student in the filtered response

### Requirement: COORDINADOR and ADMIN can filter by date range
When the actor is COORDINADOR or ADMIN, the monitor endpoint SHALL accept `fecha_desde` and `fecha_hasta` parameters to filter calificaciones by `importado_at` (F2.9).

#### Scenario: Date range filters calificaciones
- **WHEN** `fecha_desde=2026-01-01` and `fecha_hasta=2026-03-31` are provided by a COORDINADOR
- **THEN** only calificaciones with `importado_at` in that range are considered for the response

#### Scenario: PROFESOR cannot use date range filters
- **WHEN** a PROFESOR provides `fecha_desde` and `fecha_hasta`
- **THEN** those parameters are silently ignored (scope enforcement only)

#### Scenario: Date filter uses persisted import timestamp
- **WHEN** the monitor evaluates the date range for imported grades
- **THEN** it uses the persisted `importado_at` field of each `Calificacion` as source of truth

### Requirement: Monitor response is paginated
The monitor endpoint SHALL support `limit` (default 1000, max 1000) and `offset` (default 0) query parameters.

#### Scenario: Default limit applies when not specified
- **WHEN** the monitor endpoint is called without `limit`
- **THEN** at most 1000 results are returned
