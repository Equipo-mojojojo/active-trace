## ADDED Requirements

### Requirement: Lista de tareas con tabs
El sistema SHALL mostrar las tareas internas en una página con tres tabs: "Mis tareas" (asignadas al usuario actual), "Asignadas por mí" (que el usuario asignó a otros), y "Todas" (COORDINADOR/ADMIN). El tab activo SHALL persistir en el query param `?tab=mias|asignadas|todas`.

#### Scenario: Tab activo persiste en URL
- **WHEN** el usuario selecciona el tab "Asignadas por mí"
- **THEN** la URL cambia a `/coordinacion/tareas?tab=asignadas` y la tabla muestra las tareas asignadas por el usuario

#### Scenario: Tab "Todas" disponible solo para COORDINADOR/ADMIN
- **WHEN** un PROFESOR con permiso `tareas:gestionar:propio` navega a tareas
- **THEN** el tab "Todas" no se muestra o aparece deshabilitado

### Requirement: Tabla de tareas con estado y asignación
La tabla SHALL mostrar columnas: título, asignado a (avatar + nombre), asignado por (nombre), estado (badge: Pendiente=gris, En progreso=azul, Resuelta=verde, Cancelada=gris claro), fecha de creación, y botón "Ver detalle".

#### Scenario: Badges de estado semánticos
- **WHEN** una tarea tiene estado "Resuelta"
- **THEN** su badge es verde; "Pendiente" es gris; "En progreso" es azul; "Cancelada" es gris claro

#### Scenario: Estado vacío cuando no hay tareas
- **WHEN** el tab activo no tiene tareas
- **THEN** se muestra un estado vacío informativo con el texto "No tenés tareas en este momento"

### Requirement: Panel de detalle de tarea con hilo de comentarios
Al hacer click en "Ver detalle", SHALL abrirse un Drawer lateral derecho con: título, descripción, select de estado (editable), e historial de comentarios en hilo (avatar, nombre, fecha, texto). El usuario SHALL poder agregar comentarios con un campo de texto y botón "Enviar".

#### Scenario: Apertura del drawer de detalle
- **WHEN** el usuario hace click en "Ver detalle" de una tarea
- **THEN** se abre el Drawer con los datos de la tarea y el hilo de comentarios

#### Scenario: Cambio de estado desde el drawer
- **WHEN** el usuario selecciona un nuevo estado en el select del drawer y hace click en "Guardar estado"
- **THEN** el estado se actualiza en el backend y el badge de la tabla se actualiza

#### Scenario: Agregar comentario
- **WHEN** el usuario escribe un comentario y hace click en "Enviar"
- **THEN** el comentario aparece al final del hilo con el nombre y hora del usuario actual, y el campo se vacía

### Requirement: Crear y asignar tarea
El sistema SHALL permitir crear una tarea asignándola a un usuario del tenant. El formulario SHALL incluir: título (obligatorio), descripción, y campo de asignación (autocomplete de usuarios del tenant).

#### Scenario: Formulario de nueva tarea
- **WHEN** el usuario hace click en "Nueva tarea"
- **THEN** aparece un modal con los campos título, descripción, y asignar a (autocomplete)

#### Scenario: Crear tarea exitosamente
- **WHEN** el usuario completa el título y hace click en "Crear"
- **THEN** la tarea se crea en el backend y aparece en la lista del tab activo

#### Scenario: Tarea creada sin asignar queda en "Mis tareas"
- **WHEN** el usuario crea una tarea sin asignarla a nadie
- **THEN** la tarea aparece en "Mis tareas" asignada al usuario creador
