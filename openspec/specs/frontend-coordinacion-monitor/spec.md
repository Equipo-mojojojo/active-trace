## ADDED Requirements

### Requirement: Monitor institucional transversal (F2.9)
El sistema SHALL proveer una vista de monitor transversal para COORDINADOR/ADMIN que muestra el estado académico de todos los alumnos de la institución, filtrable por rango de fechas, docente, carrera y estado. La página SHALL mostrar KPIs de resumen: total de alumnos, alumnos con atrasos (badge rojo), y porcentaje al día.

#### Scenario: Visualización del monitor institucional
- **WHEN** un COORDINADOR navega a `/coordinacion/monitor`
- **THEN** ve los KPIs de resumen y la tabla con todos los alumnos de la institución

#### Scenario: KPIs reflejan el total sin filtros
- **WHEN** no hay filtros aplicados
- **THEN** los KPIs muestran los totales de toda la institución

### Requirement: Filtros del monitor institucional
El sistema SHALL permitir filtrar la tabla por: rango de fechas (date-range picker), docente (input text con búsqueda parcial), carrera (select), y estado (select: Todos/Con atrasos/Al día). Los filtros SHALL aplicarse al hacer click en "Aplicar filtros".

#### Scenario: Aplicar filtro por estado "Con atrasos"
- **WHEN** el usuario selecciona "Con atrasos" y hace click en "Aplicar filtros"
- **THEN** la tabla muestra solo los alumnos con al menos una actividad faltante

#### Scenario: Filtro por rango de fechas
- **WHEN** el usuario selecciona un rango de fechas y aplica los filtros
- **THEN** la tabla muestra el estado académico dentro de ese período

#### Scenario: Limpiar filtros
- **WHEN** el usuario hace click en "Limpiar filtros"
- **THEN** todos los filtros vuelven a su valor por defecto y la tabla muestra todos los alumnos

### Requirement: Tabla del monitor institucional con progreso visual
La tabla SHALL mostrar columnas: alumno (nombre completo), comisión (materia + cohorte), docente responsable, actividades aprobadas (barra de progreso con texto N/Total), actividades faltantes (badge circular rojo con número), estado (badge: Al día=verde, Atrasado=rojo, Sin datos=gris). La tabla SHALL ser paginada.

#### Scenario: Barra de progreso en actividades aprobadas
- **WHEN** un alumno tiene 7 de 10 actividades aprobadas
- **THEN** se muestra una barra al 70% con el texto "7/10"

#### Scenario: Badge de estado semántico
- **WHEN** un alumno tiene actividades faltantes (por debajo del umbral)
- **THEN** el badge muestra "Atrasado" en rojo

#### Scenario: Paginación de la tabla
- **WHEN** los resultados superan el límite de la página
- **THEN** se muestra la paginación al fondo con indicador "Mostrando X-Y de Z"
