## ADDED Requirements

### Requirement: COORDINADOR puede consultar todas las asignaciones del tenant con filtros
El sistema SHALL exponer `GET /api/equipos/asignaciones` que retorne todas las asignaciones del tenant con filtros opcionales por `materia_id`, `carrera_id`, `cohorte_id`, `usuario_id`, `rol` y `estado_vigencia`. Requiere permiso `equipos:asignar`.

#### Scenario: Lista asignaciones del tenant con filtros
- **WHEN** un COORDINADOR llama `GET /api/equipos/asignaciones?carrera_id=X&cohorte_id=Y`
- **THEN** el sistema retorna todas las asignaciones de esa carrera × cohorte dentro del tenant del actor autenticado

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin permiso `equipos:asignar` llama al endpoint
- **THEN** el sistema retorna `403 Forbidden`

### Requirement: COORDINADOR puede asignar múltiples docentes en bloque
El sistema SHALL exponer `POST /api/equipos/asignaciones/masiva` que cree N asignaciones en una sola transacción atómica (RN-30). El payload incluye lista de `usuario_id`, más `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `comisiones`, `responsable_id`, `desde` y `hasta`. Requiere `equipos:asignar`. Registra auditoría `ASIGNACION_MODIFICAR` por cada asignación creada.

#### Scenario: Alta masiva crea todas las asignaciones en una transacción
- **WHEN** el COORDINADOR envía una lista de 5 usuarios con el mismo contexto académico
- **THEN** el sistema crea las 5 asignaciones atómicamente y retorna `201 Created` con el detalle de cada una

#### Scenario: Conflicto en una asignación revierte toda la operación
- **WHEN** uno de los usuarios del bloque ya tiene una asignación idéntica activa (misma materia × rol × cohorte vigente)
- **THEN** el sistema revierte la transacción completa y retorna `409 Conflict` con el detalle de qué usuario generó el conflicto

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin `equipos:asignar` llama al endpoint
- **THEN** el sistema retorna `403 Forbidden`

### Requirement: COORDINADOR puede clonar un equipo entre períodos
El sistema SHALL exponer `POST /api/equipos/clonar` que duplique todas las asignaciones vigentes de un equipo origen (`materia_id`, `carrera_id`, `cohorte_id` origen) hacia un destino (misma materia × carrera × nueva `cohorte_id`) con nuevas fechas `desde`/`hasta` (RN-12). Requiere `equipos:asignar`. Registra auditoría `ASIGNACION_MODIFICAR`.

#### Scenario: Clonado crea asignaciones en el destino con nuevas fechas
- **WHEN** el COORDINADOR clona el equipo de cohorte MAR-2025 hacia AGO-2025 con desde=2025-08-01
- **THEN** el sistema crea una asignación nueva por cada asignación vigente del origen, con `cohorte_id` del destino y las fechas indicadas, sin modificar las del origen

#### Scenario: Asignación con hasta=NULL en origen recibe hasta del destino
- **WHEN** una asignación origen tiene `hasta IS NULL` (vigencia abierta)
- **THEN** la asignación clonada recibe la `hasta` del período destino especificada en el request

#### Scenario: Equipo origen sin asignaciones vigentes retorna advertencia
- **WHEN** el equipo origen no tiene asignaciones con `estado_vigencia=Vigente`
- **THEN** el sistema retorna `200 OK` con `clonadas: 0` y mensaje explicativo (no es un error)

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin `equipos:asignar` llama al endpoint
- **THEN** el sistema retorna `403 Forbidden`

### Requirement: COORDINADOR puede modificar la vigencia de un equipo en bloque
El sistema SHALL exponer `PATCH /api/equipos/vigencia` que actualice `desde`/`hasta` de todas las asignaciones de un equipo (`materia_id`, `carrera_id`, `cohorte_id`). Soporta modo `dry_run=true` que retorna el conteo de asignaciones afectadas sin ejecutar el cambio. Requiere `equipos:asignar`. Registra auditoría `ASIGNACION_MODIFICAR`.

#### Scenario: dry_run retorna conteo sin modificar datos
- **WHEN** el COORDINADOR llama con `dry_run=true`
- **THEN** el sistema retorna `200 OK` con `afectadas: N` y no modifica ninguna fila en la base de datos

#### Scenario: Sin dry_run actualiza todas las asignaciones del equipo
- **WHEN** el COORDINADOR llama sin `dry_run` con nuevas fechas
- **THEN** el sistema actualiza `desde`/`hasta` de todas las asignaciones del equipo y registra auditoría por cada una

#### Scenario: Equipo inexistente retorna 404
- **WHEN** no existe ninguna asignación con la combinación materia × carrera × cohorte indicada
- **THEN** el sistema retorna `404 Not Found`

### Requirement: COORDINADOR puede exportar el equipo docente como CSV
El sistema SHALL exponer `GET /api/equipos/export` que retorne un archivo CSV descargable con el detalle de todas las asignaciones del equipo seleccionado (docente, rol, materia, carrera, cohorte, vigencia, estado_vigencia). Requiere `equipos:asignar`.

#### Scenario: Export retorna archivo CSV válido
- **WHEN** el COORDINADOR llama `GET /api/equipos/export?materia_id=X&cohorte_id=Y`
- **THEN** el sistema retorna `200 OK` con `Content-Type: text/csv` y `Content-Disposition: attachment; filename="equipo_*.csv"` con una fila por asignación

#### Scenario: Equipo sin asignaciones retorna CSV con encabezado solamente
- **WHEN** el equipo solicitado no tiene asignaciones
- **THEN** el sistema retorna un CSV con la fila de encabezado pero sin filas de datos

### Requirement: Toda escritura sobre equipos registra auditoría ASIGNACION_MODIFICAR
El sistema SHALL llamar a `AuditService.registrar(accion=AuditAction.ASIGNACION_MODIFICAR, ...)` para cada asignación creada, clonada o con vigencia modificada. El actor auditado SHALL ser el usuario del JWT (no el docente asignado).

#### Scenario: Alta masiva genera una entrada de auditoría por asignación
- **WHEN** la asignación masiva crea 5 asignaciones
- **THEN** el sistema registra 5 entradas en `AuditLog` con `accion=ASIGNACION_MODIFICAR` y `actor_id` del coordinador

#### Scenario: Clonado genera auditoría por cada asignación clonada
- **WHEN** el clonado duplica 3 asignaciones
- **THEN** el sistema registra 3 entradas de auditoría con `accion=ASIGNACION_MODIFICAR`
