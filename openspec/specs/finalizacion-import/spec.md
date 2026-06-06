## ADDED Requirements

### Requirement: Finalization report detects textual activities without a grade
The system SHALL parse LMS completion reports (xlsx/csv) and identify students who have completed an activity (marked as finalized) but whose corresponding `Calificacion` row has no `nota_textual`. Only textual-scale activities are checked (RN-08).

#### Scenario: Student with completed textual activity and no grade is flagged
- **WHEN** a finalization report shows student A completed activity "TP1" and no `Calificacion` with `nota_textual` exists for that student × activity
- **THEN** student A × "TP1" appears in the pending-correction list

#### Scenario: Student with completed numeric activity is NOT flagged
- **WHEN** a finalization report shows student A completed a numeric activity (identified by `(Real)` suffix) and no grade exists
- **THEN** that pair does NOT appear in the pending-correction list (RN-08)

#### Scenario: Student with existing textual grade is NOT flagged
- **WHEN** a finalization report shows student A completed "TP1" AND a `Calificacion` with `nota_textual` already exists for that pair
- **THEN** student A × "TP1" does NOT appear in the pending-correction list

### Requirement: Finalization import endpoint returns pending list without persisting
`POST /api/v1/calificaciones/finalizacion/preview` SHALL return the pending-correction list as a response object. The system SHALL NOT create any new `Calificacion` rows from this operation.

#### Scenario: Response contains pending pairs only
- **WHEN** a valid completion report is uploaded
- **THEN** the response contains `{alumno, actividad}` pairs for entries where `nota_textual` is missing

### Requirement: Finalization import requires calificaciones:importar permission
The finalization preview endpoint SHALL enforce `calificaciones:importar` permission.

#### Scenario: Unauthorized user is rejected
- **WHEN** a user without `calificaciones:importar` calls the finalization endpoint
- **THEN** the system returns `403`

### Requirement: Finalización cruza pendientes contra el padrón versionado válido y calificaciones persistidas
`POST /api/v1/calificaciones/finalizacion/preview` SHALL resolver alumnos usando el padrón versionado válido para la materia/contexto solicitado y contrastar cada actividad textual completada contra las `Calificacion` persistidas del mismo alumno, sin depender de atributos académicos inexistentes en `EntradaPadron`.

#### Scenario: Preview de finalización usa el padrón activo real
- **WHEN** se procesa un reporte de finalización para una materia con padrón versionado
- **THEN** el cruce de alumnos se hace contra las `EntradaPadron` de la versión válida correspondiente

#### Scenario: Actividad textual ya corregida no aparece como pendiente
- **WHEN** una actividad textual completada ya tiene una `Calificacion` persistida para ese alumno y actividad
- **THEN** el preview no la reporta como trabajo sin corregir

#### Scenario: Versiones históricas no contaminan el resultado
- **WHEN** existen versiones históricas del padrón o calificaciones fuera del contexto vigente
- **THEN** el preview no marca pendientes en base a esas versiones ajenas al cruce actual
