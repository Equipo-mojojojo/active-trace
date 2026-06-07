## ADDED Requirements

### Requirement: Encolado crea comunicaciones pendientes listas para despacho asíncrono
Cuando un usuario confirma un envío válido, el sistema SHALL crear comunicaciones en estado `Pendiente` para que un worker asíncrono las procese.

#### Scenario: Confirmación de envío genera cola pendiente
- **WHEN** el usuario confirma un envío luego de la preview
- **THEN** se crean comunicaciones en estado `Pendiente` bajo el lote correspondiente

### Requirement: Worker procesa solo comunicaciones elegibles
El worker SHALL tomar únicamente comunicaciones que estén en estado `Pendiente` y que no requieran aprobación adicional pendiente.

#### Scenario: Worker omite comunicaciones no aprobadas
- **WHEN** un tenant exige aprobación y una comunicación sigue esperando esa aprobación
- **THEN** el worker no la pasa a `Enviando`

### Requirement: Worker registra resultado final por comunicación
El worker SHALL actualizar cada comunicación a `Enviado` o `Error` según el resultado del intento de despacho, preservando trazabilidad por mensaje.

#### Scenario: Envío exitoso actualiza estado final
- **WHEN** el canal de despacho confirma un mensaje
- **THEN** la `Comunicacion` pasa de `Enviando` a `Enviado`

#### Scenario: Error de despacho deja evidencia del fallo
- **WHEN** el canal de despacho falla para una comunicación
- **THEN** la `Comunicacion` pasa a `Error` y queda registrada la evidencia necesaria para seguimiento
