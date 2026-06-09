## ADDED Requirements

### Requirement: Lista de convocatorias de coloquio
El sistema SHALL mostrar las convocatorias de evaluación en formato de cards. Cada card SHALL mostrar: materia, instancia (1ra/2da/Final), fecha, métricas horizontales (Convocados/Reservas/Libres) y estado (Abierta=verde/Cerrada=gris).

#### Scenario: Lista de convocatorias visible
- **WHEN** un COORDINADOR navega a `/coloquios`
- **THEN** ve la lista de convocatorias activas y pasadas con sus métricas

#### Scenario: Métricas en tiempo real
- **WHEN** un alumno realiza una reserva
- **THEN** las métricas "Reservas" y "Libres" de la convocatoria se actualizan en la próxima carga

### Requirement: Crear convocatoria de coloquio
El sistema SHALL permitir crear una nueva convocatoria con los campos: materia (select), instancia (select: 1ra/2da/Final), rango de fechas disponibles, y cupo por turno (número). Al crear, la convocatoria aparece con estado "Abierta".

#### Scenario: Crear convocatoria exitosamente
- **WHEN** el usuario completa el formulario y guarda
- **THEN** la convocatoria se crea con estado "Abierta" y aparece en la lista

#### Scenario: Validación de cupo mayor a cero
- **WHEN** el usuario intenta crear una convocatoria con cupo = 0
- **THEN** el formulario muestra error "El cupo debe ser mayor a 0"

### Requirement: Panel de gestión de convocatoria (tabbed)
Al seleccionar una convocatoria, SHALL abrirse un Drawer/panel con tres tabs: "Alumnos convocados" (tabla con nombre y DNI, botón de import masivo desde archivo), "Reservas" (tabla con alumno, día/hora elegido, estado Activa/Cancelada) y "Resultados" (tabla con alumno y campo de nota/resultado editable).

#### Scenario: Tab Alumnos convocados muestra la lista
- **WHEN** el usuario abre el panel y selecciona el tab "Alumnos convocados"
- **THEN** ve la tabla de alumnos convocados con nombre y DNI

#### Scenario: Importar alumnos desde archivo
- **WHEN** el usuario hace click en "Importar desde archivo" y sube un CSV/XLSX
- **THEN** los alumnos del archivo se agregan a la convocatoria y la tabla se actualiza

#### Scenario: Tab Reservas muestra el estado actual
- **WHEN** el usuario selecciona el tab "Reservas"
- **THEN** ve la tabla con los turnos reservados, con badges "Activa" (verde) o "Cancelada" (gris)

#### Scenario: Registrar resultado de coloquio
- **WHEN** el usuario ingresa la nota en el campo de resultado de un alumno y guarda
- **THEN** el resultado se persiste en el backend

### Requirement: Cerrar convocatoria
El sistema SHALL permitir cerrar una convocatoria abierta. Una vez cerrada, no SHALL aceptar nuevas reservas y su estado SHALL cambiar a "Cerrada".

#### Scenario: Cerrar convocatoria
- **WHEN** el COORDINADOR hace click en "Cerrar convocatoria" y confirma
- **THEN** la convocatoria cambia a estado "Cerrada" y el badge de la card cambia a gris
