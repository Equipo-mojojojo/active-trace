## ADDED Requirements

### Requirement: Filtros del panel de auditoría
El sistema SHALL mostrar en `AuditoriaPage` (ruta `/admin/auditoria`) una barra de filtros con rango de fechas, dropdown de usuario, dropdown de acción y dropdown de materia. Los filtros SHALL aplicarse a las consultas de métricas como parámetros de query (`desde`, `hasta`, `actor_id`, `materia_id`). El frontend NUNCA SHALL enviar `actor_id` propio para forzar scope: cuando el usuario solo tiene `auditoria:ver:propio`, el backend restringe el scope automáticamente desde la sesión.

#### Scenario: Aplicar filtro de rango de fechas
- **WHEN** el usuario selecciona un rango de fechas
- **THEN** todas las consultas de métricas se re-ejecutan con `desde` y `hasta`

#### Scenario: Filtro por materia
- **WHEN** el usuario selecciona una materia
- **THEN** las métricas se re-consultan con `materia_id`

### Requirement: Gráfico de acciones por día
El sistema SHALL mostrar una card con un gráfico de la serie temporal de acciones (`GET /api/v1/auditoria/metricas/acciones-por-dia`), una barra/punto por día con su total.

#### Scenario: Render del gráfico con datos
- **WHEN** el panel carga con actividad en el período
- **THEN** se muestra el gráfico de acciones por día con un valor por fecha

#### Scenario: Estado vacío sin actividad
- **WHEN** no hay acciones en el rango filtrado
- **THEN** la card muestra un estado vacío informativo

### Requirement: Estado de comunicaciones por docente
El sistema SHALL mostrar una card "Estado de comunicaciones por docente" (`GET /api/v1/auditoria/metricas/estado-comunicaciones`) con la distribución de estados (Pendiente / Enviando / Enviado / Error / Cancelado) por docente, usando badges de color por estado.

#### Scenario: Mostrar distribución por docente
- **WHEN** el panel carga
- **THEN** se muestra por docente la cantidad de comunicaciones en cada estado con su badge de color

### Requirement: Interacciones por docente × materia
El sistema SHALL mostrar las interacciones agrupadas por docente, materia y acción (`GET /api/v1/auditoria/metricas/interacciones`), ordenadas por total descendente.

#### Scenario: Listar interacciones
- **WHEN** el panel carga
- **THEN** se muestran las filas de `(docente, materia, acción, total)` ordenadas por total descendente

### Requirement: Log completo de auditoría
El sistema SHALL mostrar una card "Log completo de auditoría" (`GET /api/v1/auditoria/metricas/ultimas-acciones`) con las últimas N acciones (default 200, cap del backend respetado), con columnas: fecha y hora, usuario, materia, acción, registros afectados, IP, user agent.

#### Scenario: Render del log con default
- **WHEN** el panel carga sin parámetro de límite
- **THEN** se muestran hasta 200 registros más recientes con todos sus campos

#### Scenario: Límite mayor al máximo se capea sin error
- **WHEN** se solicita un límite mayor al máximo del backend
- **THEN** el backend retorna el cap y la tabla los muestra sin error

### Requirement: Protección de acceso a auditoría
La ruta `/admin/auditoria` SHALL estar protegida por `AuthGuard` + `PermissionGuard` aceptando `auditoria:ver` o `auditoria:ver:propio`.

#### Scenario: Acceso sin permiso de auditoría
- **WHEN** un usuario sin `auditoria:ver` ni `auditoria:ver:propio` navega a `/admin/auditoria`
- **THEN** la app redirige a `/403`

#### Scenario: COORDINADOR con scope propio
- **WHEN** un COORDINADOR con solo `auditoria:ver:propio` abre el panel
- **THEN** ve el panel con los datos ya restringidos por el backend a su propia actividad, sin que el frontend envíe su `actor_id`
