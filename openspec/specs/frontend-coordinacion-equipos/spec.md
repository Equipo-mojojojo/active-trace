## ADDED Requirements

### Requirement: Lista de equipos docentes con filtros
El sistema SHALL mostrar una tabla de asignaciones docentes filtrable por cohorte y materia. Cada fila SHALL mostrar: nombre del docente, rol (badge con color), materias asignadas (chips), rango de vigencia y estado (Activo/Vencido).

#### Scenario: Lista visible con datos
- **WHEN** un COORDINADOR navega a `/coordinacion/equipos`
- **THEN** ve la tabla de asignaciones con filtros de cohorte y materia en el header

#### Scenario: Filtrado por cohorte y materia
- **WHEN** el usuario selecciona una cohorte y/o materia en los dropdowns del header
- **THEN** la tabla se actualiza mostrando solo las asignaciones que coinciden con los filtros

#### Scenario: Estado Activo/Vencido calculado por vigencia
- **WHEN** la asignación tiene fecha `hasta` en el pasado
- **THEN** el badge de estado muestra "Vencido" en gris; si sigue vigente, muestra "Activo" en verde

### Requirement: Crear y editar asignación individual
El sistema SHALL permitir crear o editar una asignación docente desde un Drawer lateral derecho. El formulario SHALL incluir: docente (autocomplete), rol (select), materias (multi-select), vigencia desde/hasta. Al guardar con éxito, SHALL cerrar el drawer e invalidar la lista.

#### Scenario: Apertura del drawer para nueva asignación
- **WHEN** el usuario hace click en "Asignar docente"
- **THEN** se abre el Drawer lateral con el formulario vacío

#### Scenario: Apertura del drawer para editar asignación existente
- **WHEN** el usuario hace click en "Editar" en una fila de la tabla
- **THEN** se abre el Drawer lateral con los datos de esa asignación precargados

#### Scenario: Guardar asignación exitosamente
- **WHEN** el usuario completa el formulario y hace click en "Guardar"
- **THEN** la asignación se crea/actualiza en el backend, el drawer se cierra y la tabla se actualiza

#### Scenario: Validación de campos obligatorios
- **WHEN** el usuario intenta guardar sin docente o sin rol
- **THEN** el formulario muestra mensajes de error en los campos vacíos y no envía la request

### Requirement: Asignación masiva de docentes
El sistema SHALL proveer un modal de asignación masiva que permita seleccionar un bloque de docentes y asignarlos a múltiples materias con un rol y vigencia comunes.

#### Scenario: Apertura del modal masivo
- **WHEN** el usuario hace click en "Asignación masiva"
- **THEN** se abre un modal con campos: docentes (multi-select), rol (select), materias (multi-select), vigencia desde/hasta

#### Scenario: Confirmación de asignación masiva
- **WHEN** el usuario completa los campos del modal y confirma
- **THEN** se crean las asignaciones en el backend y la tabla se actualiza con todos los nuevos registros

### Requirement: Clonar equipo desde período anterior
El sistema SHALL permitir clonar el equipo docente activo de un período anterior al período actual, ajustando la vigencia.

#### Scenario: Click en "Clonar equipo"
- **WHEN** el usuario hace click en "Clonar equipo desde período anterior"
- **THEN** se abre un diálogo de confirmación indicando qué equipo se va a clonar y cuál será la nueva vigencia

#### Scenario: Confirmación del clonado
- **WHEN** el usuario confirma el clonado
- **THEN** se crean las asignaciones del período anterior con las nuevas fechas y la tabla se actualiza

### Requirement: Exportar equipo a archivo
El sistema SHALL permitir exportar la lista actual de asignaciones a un archivo descargable (CSV).

#### Scenario: Export del equipo
- **WHEN** el usuario hace click en "Exportar"
- **THEN** el navegador descarga un archivo CSV con todas las asignaciones visibles (filtros aplicados)
