## ADDED Requirements

### Requirement: El sistema SHALL permitir iniciar impersonación

El sistema SHALL exponer `POST /api/admin/impersonacion/iniciar` protegido con `require_permission("impersonacion:usar")` que recibe `usuario_id` (UUID del usuario a impersonar) y devuelve un JWT access con claims adicionales que indican impersonación activa.

#### Scenario: Iniciar impersonación exitosamente
- **WHEN** un usuario ADMIN con permiso `impersonacion:usar` solicita iniciar impersonación del usuario TECNICO
- **THEN** el sistema SHALL devolver status 200
- **THEN** el sistema SHALL devolver un nuevo JWT access con `es_impersonacion: true` e `impersonado_id`
- **THEN** el sistema SHALL registrar un evento `IMPERSONACION_INICIAR` en audit_log con actor_id=ADMIN, impersonado_id=TECNICO

#### Scenario: Iniciar impersonación sin permiso recibe 403
- **WHEN** un usuario SIN permiso `impersonacion:usar` solicita iniciar impersonación
- **THEN** el sistema SHALL devolver status 403

#### Scenario: Iniciar impersonación de usuario inexistente recibe 404
- **WHEN** se solicita impersonar un usuario_id que no existe en el tenant
- **THEN** el sistema SHALL devolver status 404

### Requirement: El sistema SHALL permitir finalizar impersonación

El sistema SHALL exponer `POST /api/admin/impersonacion/finalizar` que recibe el JWT de impersonación activa, invalida la sesión y devuelve un JWT access normal del actor real.

#### Scenario: Finalizar impersonación exitosamente
- **WHEN** un usuario bajo impersonación solicita finalizarla
- **THEN** el sistema SHALL devolver status 200 con un nuevo JWT access normal (sin claims de impersonación)
- **THEN** el sistema SHALL registrar un evento `IMPERSONACION_FINALIZAR` en audit_log

### Requirement: Las acciones bajo impersonación SHALL atribuirse al actor real

Cuando un request se ejecuta con un JWT que tiene `es_impersonacion: true`, el sistema `get_current_user` SHALL cargar los datos del usuario impersonado (para permisos), pero el `AuditService` SHALL usar `actor_id` del usuario real y `impersonado_id` del usuario impersonado.

#### Scenario: Obtener current_user bajo impersonación
- **WHEN** el request usa un JWT con `es_impersonacion: true`
- **THEN** `get_current_user` SHALL devolver el usuario impersonado (para evaluar permisos)
- **THEN** `request.state.actor_real` SHALL ser el usuario real (quien impersona)

### Requirement: La sesión bajo impersonación SHALL ser distinguible

El sistema SHALL indicar visual y técnicamente que la sesión actual es de impersonación. A nivel técnico, el JWT access incluye `es_impersonacion: true`.

#### Scenario: JWT de impersonación incluye claim
- **WHEN** se decodifica un JWT emitido durante impersonación
- **THEN** el payload SHALL contener `es_impersonacion: true`
- **THEN** el payload SHALL contener `impersonado_id` con el UUID del usuario impersonado
