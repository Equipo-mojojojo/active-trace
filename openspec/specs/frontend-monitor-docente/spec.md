## ADDED Requirements

### Requirement: Monitor de seguimiento de alumnos (F2.8)
El sistema SHALL proveer a TUTOR y PROFESOR una tabla filtrable con el estado de actividades de los alumnos asignados. Los filtros disponibles son: alumno (búsqueda por nombre o correo), comisión, actividad y mínimo de actividad cumplida (porcentaje).

#### Scenario: Vista por defecto sin filtros
- **WHEN** el usuario con rol TUTOR o PROFESOR navega a `/monitor`
- **THEN** el sistema muestra la tabla con todos los alumnos asignados y su estado de actividades actual

#### Scenario: Filtro por comisión
- **WHEN** el usuario selecciona una comisión en el filtro
- **THEN** la tabla se actualiza mostrando solo los alumnos de esa comisión

#### Scenario: Filtro por mínimo de actividad cumplida
- **WHEN** el usuario ingresa un porcentaje mínimo (ej: 50%)
- **THEN** la tabla muestra solo los alumnos que superan ese umbral de actividades cumplidas

#### Scenario: Búsqueda por alumno
- **WHEN** el usuario escribe en el campo de búsqueda
- **THEN** la tabla filtra en tiempo real (debounce 300ms) por nombre o correo del alumno

#### Scenario: Acceso denegado a otros roles
- **WHEN** un usuario con rol ALUMNO o FINANZAS navega a `/monitor`
- **THEN** el PermissionGuard redirige a `/403`
