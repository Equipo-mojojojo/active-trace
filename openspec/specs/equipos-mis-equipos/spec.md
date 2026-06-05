## ADDED Requirements

### Requirement: Docente puede ver sus propias asignaciones activas e históricas
El sistema SHALL exponer un endpoint `GET /api/equipos/mis-equipos` que retorne todas las asignaciones del usuario autenticado dentro de su tenant, con `estado_vigencia` derivado en tiempo real (Vigente / Vencida), y filtros opcionales por `estado`, `materia_id`, `rol`, `carrera_id` y `cohorte_id`.

#### Scenario: Docente ve sus asignaciones vigentes
- **WHEN** un usuario autenticado con rol PROFESOR llama `GET /api/equipos/mis-equipos`
- **THEN** el sistema retorna solo las asignaciones cuyo `tenant_id` coincide con el del JWT y cuyo `usuario_id` coincide con el actor autenticado

#### Scenario: Estado de vigencia se deriva en tiempo real
- **WHEN** una asignación tiene `hasta < hoy`
- **THEN** el sistema retorna `estado_vigencia: "Vencida"` sin modificar el registro en base de datos

#### Scenario: Filtro por estado funciona correctamente
- **WHEN** el docente llama con `?estado=Vigente`
- **THEN** el sistema retorna solo asignaciones cuyo `estado_vigencia` derivado sea `Vigente`

#### Scenario: Aislamiento multi-tenant estricto
- **WHEN** el docente pertenece al tenant A
- **THEN** el sistema no retorna ninguna asignación del tenant B, aunque el usuario exista en ambos

#### Scenario: Sin asignaciones el endpoint retorna lista vacía
- **WHEN** el docente autenticado no tiene asignaciones registradas
- **THEN** el sistema retorna `200 OK` con `data: []`

### Requirement: El endpoint de mis-equipos no requiere permiso adicional
El sistema SHALL permitir que cualquier usuario autenticado acceda a `GET /api/equipos/mis-equipos` sin guard de permiso extra, ya que el scope se limita automáticamente al propio usuario por identidad de sesión.

#### Scenario: Acceso con JWT válido sin permiso especial
- **WHEN** un usuario con JWT válido llama al endpoint sin el permiso `equipos:asignar`
- **THEN** el sistema retorna `200 OK` con las asignaciones propias del usuario
