## ADDED Requirements

### Requirement: La aprobación de comunicaciones es configurable por tenant
El sistema SHALL respetar el flag `requiere_aprobacion_comunicaciones` del tenant. Si está activo, los mensajes encolados permanecen en `Pendiente` hasta recibir aprobación explícita de un usuario con `comunicacion:aprobar`.

#### Scenario: Tenant sin aprobación requerida — mensajes procesados directamente
- **WHEN** `tenant.requiere_aprobacion_comunicaciones = false` y se encolan mensajes
- **THEN** el worker los procesa sin esperar aprobación

#### Scenario: Tenant con aprobación requerida — mensajes esperan aprobación
- **WHEN** `tenant.requiere_aprobacion_comunicaciones = true` y se encolan mensajes
- **THEN** los mensajes quedan en `Pendiente` con `aprobado_por = null` hasta que se aprueben

### Requirement: Un aprobador puede aprobar o rechazar un lote completo
`POST /api/v1/comunicaciones/lotes/{lote_id}/aprobar` y `POST /api/v1/comunicaciones/lotes/{lote_id}/rechazar` SHALL requerir `comunicacion:aprobar` y actualizar todos los mensajes del lote.

#### Scenario: Aprobación de lote habilita el procesamiento por el worker
- **WHEN** un aprobador llama a `aprobar` sobre un `lote_id`
- **THEN** todos los mensajes del lote quedan con `aprobado_por = {actor_id}` y el worker los procesa en el siguiente ciclo

#### Scenario: Rechazo de lote cancela todos los mensajes
- **WHEN** un aprobador llama a `rechazar` sobre un `lote_id`
- **THEN** todos los mensajes del lote pasan a estado `Cancelado`

#### Scenario: Solo usuarios con comunicacion:aprobar pueden aprobar
- **WHEN** un usuario sin `comunicacion:aprobar` intenta aprobar un lote
- **THEN** el sistema retorna `403`

### Requirement: Un aprobador puede aprobar o rechazar mensajes individuales
`POST /api/v1/comunicaciones/{id}/aprobar` y `POST /api/v1/comunicaciones/{id}/rechazar` SHALL permitir aprobación/rechazo mensaje a mensaje.

#### Scenario: Aprobación individual no afecta otros mensajes del lote
- **WHEN** se aprueba un único mensaje de un lote de 5
- **THEN** solo ese mensaje queda con `aprobado_por` seteado; los otros 4 permanecen sin aprobar

### Requirement: Las acciones de aprobación generan audit
El sistema SHALL registrar `COMUNICACION_APROBAR` y `COMUNICACION_RECHAZAR` en el audit log al aprobar o rechazar lotes o mensajes individuales.

#### Scenario: Aprobación de lote genera audit
- **WHEN** se aprueba un lote de 10 mensajes
- **THEN** se genera un `AuditLog` con `accion = COMUNICACION_APROBAR` y `filas_afectadas = 10`
