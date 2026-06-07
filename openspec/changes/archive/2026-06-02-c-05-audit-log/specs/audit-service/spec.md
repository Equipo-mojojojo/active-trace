## ADDED Requirements

### Requirement: El sistema SHALL proveer un AuditService para registrar acciones

El sistema SHALL implementar `AuditService` como capa de servicio que recibe los datos de la acción y persiste el registro en `audit_log`. Debe estar disponible como dependencia FastAPI inyectable.

#### Scenario: Registrar acción con todos los campos
- **WHEN** el AuditService.register() recibe actor_id, tenant_id, accion, detalle, filas_afectadas
- **THEN** el sistema SHALL persistir un registro en audit_log con esos datos
- **THEN** el sistema SHALL agregar ip y user_agent desde el RequestContext capturado por el middleware

#### Scenario: Registrar acción sin detalle ni filas_afectadas
- **WHEN** el AuditService.register() recibe solo actor_id, tenant_id y accion
- **THEN** el sistema SHALL persistir el registro con detalle=NULL y filas_afectadas=NULL

### Requirement: El AuditService SHALL atribuir acciones al actor real bajo impersonación

Cuando hay impersonación activa, `AuditService` SHALL usar `actor_id` = usuario real (quien impersona) y `impersonado_id` = usuario impersonado.

#### Scenario: Registrar acción bajo impersonación
- **WHEN** el usuario ADMIN (actor real) impersona al usuario SOPORTE (impersonado)
- **WHEN** ADMIN ejecuta una acción durante la impersonación
- **THEN** audit_log.actor_id SHALL ser el ID del ADMIN
- **THEN** audit_log.impersonado_id SHALL ser el ID de SOPORTE

### Requirement: El AuditService SHALL rechazar códigos de acción inválidos

El servicio SHALL validar que el código de acción pertenezca al catálogo definido (`AuditAction`). Si no, SHALL lanzar `ValueError`.

#### Scenario: Código inválido lanza error
- **WHEN** AuditService.register() recibe accion="CODIGO_INEXISTENTE"
- **THEN** el sistema SHALL lanzar ValueError
- **THEN** NO SHALL persistir ningún registro
