## ADDED Requirements

### Requirement: Preview y selección de destinatarios antes de enviar
El sistema SHALL mostrar al PROFESOR, antes de enviar cualquier comunicación masiva, una vista de dos columnas: (izquierda) lista de destinatarios con checkbox individual por alumno y contador total; (derecha) preview del asunto y cuerpo del mensaje personalizado. Si el tenant requiere aprobación, se muestra un badge "Requiere aprobación".

#### Scenario: Preview con destinatarios seleccionados
- **WHEN** el PROFESOR selecciona alumnos atrasados y navega a la pantalla de comunicación
- **THEN** el sistema muestra la lista de destinatarios con checkboxes marcados, el preview del mensaje y el contador "N alumnos seleccionados"

#### Scenario: Deselección individual de destinatario
- **WHEN** el PROFESOR desmarca un alumno en la lista de destinatarios
- **THEN** el contador se actualiza y ese alumno no es incluido en el envío

#### Scenario: Tenant con aprobación requerida
- **WHEN** el tenant tiene configurado `requiere_aprobacion: true`
- **THEN** el sistema muestra un badge "Requiere aprobación" en lugar del botón de envío directo, y el botón envía a la cola en estado Pendiente esperando aprobación

#### Scenario: Sin destinatarios seleccionados
- **WHEN** el PROFESOR intenta enviar sin ningún destinatario marcado
- **THEN** el botón de envío está deshabilitado y se muestra una validación inline

---

### Requirement: Envío de comunicación a la cola
El sistema SHALL enviar la comunicación al endpoint de creación de comunicaciones, incluyendo los IDs de los destinatarios seleccionados y el contenido del mensaje. Al confirmar, el sistema redirige al tracking de comunicaciones.

#### Scenario: Envío exitoso
- **WHEN** el PROFESOR confirma el envío con al menos un destinatario seleccionado
- **THEN** el sistema llama a `POST /api/v1/comunicaciones/` y redirige a la pantalla de tracking

#### Scenario: Error de red al enviar
- **WHEN** la llamada al endpoint falla (error 5xx o timeout)
- **THEN** el sistema muestra un mensaje de error y permite reintentar sin perder la selección

---

### Requirement: Tracking de estado de comunicaciones en tiempo real
El sistema SHALL mostrar en la pantalla de tracking una tabla con todas las comunicaciones del PROFESOR, con estado actualizado automáticamente mediante polling cada 5 segundos mientras existan comunicaciones en estado no-terminal (Pendiente o Enviando). El polling se detiene cuando todas son terminales (OK, Fallido, Cancelado).

#### Scenario: Comunicaciones en estado mixto
- **WHEN** hay comunicaciones en estado Pendiente o Enviando
- **THEN** la tabla se refresca cada 5 segundos y los badges de estado se actualizan en tiempo real

#### Scenario: Todas las comunicaciones en estado terminal
- **WHEN** todas las comunicaciones son OK, Fallido o Cancelado
- **THEN** el polling se detiene (sin requests adicionales al backend)

#### Scenario: Filtro por estado
- **WHEN** el PROFESOR selecciona un estado en el filtro de la tabla
- **THEN** la tabla muestra solo las comunicaciones con ese estado

#### Scenario: Resumen de contadores
- **WHEN** el PROFESOR accede a la pantalla de tracking
- **THEN** el sistema muestra contadores resumen: "N enviados · M pendientes · K fallidos"

#### Scenario: Acceso denegado sin permiso
- **WHEN** un usuario sin permiso `comunicacion:enviar` navega a la pantalla de comunicación
- **THEN** el PermissionGuard redirige a `/403`
