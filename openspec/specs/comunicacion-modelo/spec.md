## ADDED Requirements

### Requirement: El modelo Comunicacion representa un mensaje saliente con ciclo de vida completo
El sistema SHALL mantener una tabla `comunicacion` con los campos del E21: `id`, `tenant_id`, `enviado_por` (FK Usuario), `materia_id` (FK Materia), `destinatario` (cifrado AES-256), `asunto`, `cuerpo`, `estado`, `lote_id`, `enviado_at`.

#### Scenario: Comunicacion persiste con todos los campos obligatorios
- **WHEN** se crea una `Comunicacion` con `enviado_por`, `materia_id`, `destinatario`, `asunto` y `cuerpo`
- **THEN** queda persistida con `estado = Pendiente` y `enviado_at = null`

#### Scenario: El destinatario no aparece en texto plano en la base de datos
- **WHEN** se persiste una `Comunicacion` con `destinatario = "alumno@test.com"`
- **THEN** el valor almacenado en la columna `destinatario` es el texto cifrado, no el email en claro

### Requirement: La máquina de estados de Comunicacion valida transiciones antes de aplicarlas
El modelo SHALL implementar métodos de transición (`marcar_enviando`, `marcar_enviado`, `marcar_error`, `cancelar`) que lancen `InvalidStateTransitionError` si la transición no es válida desde el estado actual.

#### Scenario: Transición válida Pendiente → Enviando
- **WHEN** se llama `marcar_enviando()` sobre una `Comunicacion` en estado `Pendiente`
- **THEN** el estado pasa a `Enviando` sin error

#### Scenario: Transición inválida Enviado → Enviando
- **WHEN** se llama `marcar_enviando()` sobre una `Comunicacion` en estado `Enviado`
- **THEN** se lanza `InvalidStateTransitionError`

#### Scenario: Cancelación solo desde Pendiente
- **WHEN** se llama `cancelar()` sobre una `Comunicacion` en estado `Pendiente`
- **THEN** el estado pasa a `Cancelado`

#### Scenario: Cancelación desde Enviando falla
- **WHEN** se llama `cancelar()` sobre una `Comunicacion` en estado `Enviando`
- **THEN** se lanza `InvalidStateTransitionError`

#### Scenario: Transición Enviando → Enviado registra timestamp
- **WHEN** se llama `marcar_enviado()` sobre una `Comunicacion` en estado `Enviando`
- **THEN** el estado pasa a `Enviado` y `enviado_at` queda registrado con la fecha-hora actual

### Requirement: El campo destinatario no se incluye en logs del sistema
El sistema SHALL garantizar que el valor descifrado de `destinatario` no aparezca en ninguna salida de logs, independientemente del nivel de log configurado.

#### Scenario: Email del destinatario ausente en logs de creación
- **WHEN** se crea una `Comunicacion` y el sistema tiene logs en nivel DEBUG
- **THEN** el email del destinatario no aparece en ninguna línea de log generada

### Requirement: El lote_id agrupa mensajes del mismo envío masivo
El sistema SHALL permitir asignar un `lote_id` común a múltiples `Comunicacion` creadas en una misma operación de envío masivo.

#### Scenario: Mensajes del mismo lote comparten lote_id
- **WHEN** se envían comunicaciones a 10 alumnos en una sola operación
- **THEN** todas las `Comunicacion` creadas tienen el mismo `lote_id`

#### Scenario: Comunicacion individual no requiere lote_id
- **WHEN** se crea una `Comunicacion` sin especificar `lote_id`
- **THEN** se persiste con `lote_id = null` sin error
