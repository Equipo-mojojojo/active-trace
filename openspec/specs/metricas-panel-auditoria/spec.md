## ADDED Requirements

### Requirement: Acciones por día (serie temporal de actividad)
El sistema SHALL exponer via `GET /api/v1/auditoria/metricas/acciones-por-dia` una serie temporal de conteo de acciones en `AuditLog`, agrupada por fecha, scoped al tenant del usuario autenticado. Soporta filtros opcionales de rango de fechas, materia y usuario.

#### Scenario: Obtener acciones por día sin filtros
- **WHEN** un ADMIN hace GET a `/api/v1/auditoria/metricas/acciones-por-dia`
- **THEN** el sistema retorna 200 con una lista de `{fecha, total}` para cada día con actividad en el tenant

#### Scenario: Filtrar por rango de fechas
- **WHEN** se agrega `?desde=2026-05-01&hasta=2026-05-31`
- **THEN** solo se retornan fechas dentro de ese rango

#### Scenario: Filtrar por usuario
- **WHEN** se agrega `?actor_id={uuid}`
- **THEN** solo se cuentan acciones de ese usuario

#### Scenario: COORDINADOR con auditoria:ver:propio solo ve su actividad
- **WHEN** un COORDINADOR con solo `auditoria:ver:propio` accede al endpoint
- **THEN** el sistema aplica automáticamente `actor_id = current_user.id` sin exponerlo como parámetro

#### Scenario: Sin permiso retorna 403
- **WHEN** un usuario sin `auditoria:ver` ni `auditoria:ver:propio` accede
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Estado de comunicaciones por docente
El sistema SHALL exponer via `GET /api/v1/auditoria/metricas/estado-comunicaciones` la distribución de estados de la tabla `comunicacion` (Pendiente / Enviando / Enviado / Error / Cancelado) agrupada por `actor_id` (docente que generó el lote), scoped al tenant.

#### Scenario: Obtener distribución de estados
- **WHEN** un ADMIN hace GET a `/api/v1/auditoria/metricas/estado-comunicaciones`
- **THEN** el sistema retorna 200 con lista de `{actor_id, estado, total}` por combinación docente×estado

#### Scenario: Filtrar por materia
- **WHEN** se agrega `?materia_id={uuid}`
- **THEN** solo se cuentan comunicaciones asociadas a esa materia

#### Scenario: COORDINADOR scope propio en estado-comunicaciones
- **WHEN** un COORDINADOR con `auditoria:ver:propio` accede
- **THEN** solo se retornan comunicaciones donde el docente es el propio COORDINADOR

### Requirement: Interacciones por docente × materia
El sistema SHALL exponer via `GET /api/v1/auditoria/metricas/interacciones` el conteo de acciones del `AuditLog` agrupado por `(actor_id, materia_id, accion)`, scoped al tenant.

#### Scenario: Obtener interacciones
- **WHEN** un ADMIN hace GET a `/api/v1/auditoria/metricas/interacciones`
- **THEN** el sistema retorna 200 con lista de `{actor_id, materia_id, accion, total}` ordenado por total descendente

#### Scenario: Filtrar por docente específico
- **WHEN** se agrega `?actor_id={uuid}`
- **THEN** solo se retornan filas de ese docente

#### Scenario: Filtrar por rango de fechas
- **WHEN** se agrega `?desde` y `?hasta`
- **THEN** solo se cuentan acciones en ese rango temporal

### Requirement: Log de últimas acciones con límite configurable
El sistema SHALL exponer via `GET /api/v1/auditoria/metricas/ultimas-acciones` los N registros más recientes del `AuditLog` del tenant, ordenados por `fecha_hora DESC`. El parámetro `?limite=N` controla la cantidad; el máximo permitido es 200 (configurable en settings). Si se omite, el default es 200.

#### Scenario: Obtener últimas acciones con default
- **WHEN** un ADMIN hace GET a `/api/v1/auditoria/metricas/ultimas-acciones`
- **THEN** el sistema retorna los 200 registros más recientes del tenant

#### Scenario: Solicitar límite menor al máximo
- **WHEN** se agrega `?limite=50`
- **THEN** el sistema retorna los 50 registros más recientes

#### Scenario: Solicitar límite mayor al máximo permitido
- **WHEN** se agrega `?limite=500` y el máximo configurado es 200
- **THEN** el sistema aplica el cap y retorna 200 registros (sin error — silently capped)

#### Scenario: Filtrar por materia en últimas acciones
- **WHEN** se agrega `?materia_id={uuid}`
- **THEN** solo se retornan acciones de esa materia dentro del límite

#### Scenario: COORDINADOR scope propio en últimas acciones
- **WHEN** un COORDINADOR con `auditoria:ver:propio` accede
- **THEN** solo se retornan sus propias acciones dentro del límite

### Requirement: Permisos del panel de métricas
Todos los endpoints de métricas SHALL requerir `auditoria:ver` o `auditoria:ver:propio`. Con `auditoria:ver:propio` el scope se restringe automáticamente al usuario autenticado.

#### Scenario: Acceso sin autenticación retorna 401
- **WHEN** una petición no autenticada llega a cualquier endpoint `/api/v1/auditoria/metricas/`
- **THEN** el sistema retorna 401 Unauthorized

#### Scenario: Acceso sin ningún permiso de auditoría retorna 403
- **WHEN** un usuario sin `auditoria:ver` ni `auditoria:ver:propio` accede
- **THEN** el sistema retorna 403 Forbidden
