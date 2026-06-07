## ADDED Requirements

### Requirement: Preview es obligatoria antes de encolar comunicaciones
El sistema SHALL ofrecer una vista previa del asunto y cuerpo final de cada comunicación antes de permitir su encolado.

#### Scenario: Preview muestra contenido renderizado por destinatario
- **WHEN** un usuario solicita preview para uno o más alumnos seleccionados
- **THEN** el sistema devuelve el asunto y cuerpo renderizados con las variables aplicadas para cada destinatario

### Requirement: Preview no persiste comunicaciones definitivas
La operación de preview SHALL calcular contenido y destinatarios sin crear filas `Comunicacion` persistidas en la cola.

#### Scenario: Preview no deja mensajes pendientes
- **WHEN** el usuario ejecuta la preview pero no confirma el envío
- **THEN** no existe ninguna `Comunicacion` nueva en estado `Pendiente`

### Requirement: Preview requiere permiso de comunicación
Los endpoints de preview SHALL exigir el permiso `comunicacion:enviar` y limitar destinatarios al scope del actor autenticado.

#### Scenario: Profesor no puede previsualizar alumnos fuera de su scope
- **WHEN** un PROFESOR intenta generar preview para alumnos de una materia donde no tiene asignación vigente
- **THEN** el sistema rechaza la operación
