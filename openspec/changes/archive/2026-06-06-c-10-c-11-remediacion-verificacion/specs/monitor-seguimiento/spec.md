## MODIFIED Requirements

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
