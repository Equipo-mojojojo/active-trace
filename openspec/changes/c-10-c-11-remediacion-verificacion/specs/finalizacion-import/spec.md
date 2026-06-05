## ADDED Requirements

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
