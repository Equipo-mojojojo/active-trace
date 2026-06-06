## ADDED Requirements

### Requirement: El worker procesa mensajes en estado Pendiente y los transiciona a Enviado o Error
El worker asíncrono SHALL consultar periódicamente la tabla `comunicacion` buscando mensajes con `estado = Pendiente` (y `aprobado_por IS NOT NULL` si el tenant requiere aprobación), marcarlos como `Enviando`, intentar el envío y transicionarlos a `Enviado` o `Error`.

#### Scenario: Worker procesa mensaje Pendiente exitosamente
- **WHEN** existe una `Comunicacion` en estado `Pendiente` y el worker ejecuta su loop
- **THEN** el mensaje transiciona `Pendiente → Enviando → Enviado` y `enviado_at` queda registrado

#### Scenario: Worker marca Error ante fallo de envío
- **WHEN** el intento de envío falla (simulado) para una `Comunicacion` en estado `Enviando`
- **THEN** el mensaje transiciona a `Error`

#### Scenario: Worker no procesa mensajes de otro tenant
- **WHEN** existen mensajes `Pendiente` de dos tenants distintos y el worker procesa el tenant A
- **THEN** solo los mensajes del tenant A son procesados; los del tenant B permanecen `Pendiente`

### Requirement: El worker respeta el límite de reintentos antes de marcar Error definitivo
El worker SHALL reintentar el envío hasta `WORKER_MAX_RETRIES` veces (default 3) con backoff antes de marcar el mensaje como `Error`.

#### Scenario: Mensaje pasa a Error tras agotar reintentos
- **WHEN** un mensaje falla `WORKER_MAX_RETRIES` veces consecutivas
- **THEN** el estado final es `Error` y no se reintenta más

#### Scenario: Mensaje pasa a Enviado en reintento exitoso
- **WHEN** un mensaje falla en el primer intento pero tiene éxito en el segundo
- **THEN** el estado final es `Enviado`

### Requirement: Mensajes en estado Enviando al reiniciar el worker son recuperados
El worker SHALL, al iniciar, detectar mensajes en estado `Enviando` con `updated_at` anterior al timeout configurado y marcarlos como `Error` para que puedan ser reintentados manualmente o ignorados.

#### Scenario: Worker recupera mensajes huérfanos en Enviando
- **WHEN** el worker inicia y encuentra mensajes con `estado = Enviando` y `updated_at` > timeout
- **THEN** los marca como `Error` con detalle "worker_restart_recovery"
