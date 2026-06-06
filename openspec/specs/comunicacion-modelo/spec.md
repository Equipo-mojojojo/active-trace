## ADDED Requirements

### Requirement: Comunicación persiste una fila por destinatario con trazabilidad de lote
El sistema SHALL persistir cada comunicación saliente a alumnos como una entidad `Comunicacion` individual con `tenant_id`, `lote_id`, destinatario cifrado y referencia al contexto académico necesario para auditar el envío.

#### Scenario: Envío masivo crea múltiples comunicaciones bajo un lote
- **WHEN** un usuario encola un recordatorio para varios alumnos
- **THEN** el sistema crea una fila `Comunicacion` por destinatario y todas comparten el mismo `lote_id`

### Requirement: Destinatario y contenido sensible se almacenan cifrados
Los datos sensibles del destinatario SHALL almacenarse cifrados en reposo y no deben exponerse en texto plano fuera de la capa autorizada de lectura.

#### Scenario: Persistencia de destinatario no guarda email plano
- **WHEN** se crea una `Comunicacion`
- **THEN** el email u otro identificador sensible del destinatario queda cifrado en la persistencia

### Requirement: Comunicación usa máquina de estados explícita
Cada `Comunicacion` SHALL mantener un estado del ciclo `Pendiente`, `Enviando`, `Enviado`, `Error` o `Cancelado`, con transiciones válidas controladas por reglas de dominio.

#### Scenario: Comunicación pendiente puede cancelarse
- **WHEN** una comunicación está en estado `Pendiente` y un actor autorizado la cancela
- **THEN** su estado pasa a `Cancelado`

#### Scenario: Comunicación ya enviada no puede volver a pendiente
- **WHEN** una comunicación está en estado `Enviado`
- **THEN** el sistema rechaza cualquier transición que intente volverla a `Pendiente`
