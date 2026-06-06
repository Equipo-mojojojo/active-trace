## ADDED Requirements

### Requirement: Alumno atrasado defined by missing or below-threshold grade
The system SHALL classify a student as "atrasado" for a materia if at least one of these conditions holds (RN-06):
- The student has no `Calificacion` row for an activity that exists for other students in the same materia (faltante).
- The student has at least one `Calificacion` with `aprobado=False`.

#### Scenario: Student with a failing grade is atrasado
- **WHEN** a student has one `Calificacion` with `aprobado=False` in a materia
- **THEN** that student appears in the atrasados list for that materia

#### Scenario: Student with all passing grades is not atrasado
- **WHEN** all `Calificacion` rows for a student in a materia have `aprobado=True`
- **THEN** that student does NOT appear in the atrasados list

#### Scenario: Student missing an activity present for others is atrasado
- **WHEN** activity "TP1" has `Calificacion` rows for other students but not for student A
- **THEN** student A appears in the atrasados list (faltante condition)

#### Scenario: Student with no calificaciones at all is atrasado when others have them
- **WHEN** other students have calificaciones for a materia but student A has none
- **THEN** student A is considered atrasado (all activities are faltantes)

### Requirement: Atrasados endpoint requires atrasados:ver permission
`GET /api/v1/analisis/atrasados` SHALL enforce the `atrasados:ver` permission. TUTOR, PROFESOR, COORDINADOR, and ADMIN SHALL have this permission by default.

#### Scenario: User without permission is rejected
- **WHEN** a user without `atrasados:ver` calls the endpoint
- **THEN** the system returns `403`

### Requirement: Atrasados endpoint supports filtering by materia, cohorte and comision
The endpoint SHALL accept optional query parameters `materia_id`, `cohorte_id`, and `comision`. When provided, results are filtered to match.

#### Scenario: Filter by materia_id returns only that materia's atrasados
- **WHEN** `materia_id` is provided in the query
- **THEN** only students whose atrasado condition comes from that materia are returned
