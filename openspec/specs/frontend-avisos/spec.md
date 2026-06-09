## ADDED Requirements

### Requirement: Lista de avisos para COORDINADOR/ADMIN
El sistema SHALL mostrar los avisos institucionales del tenant en formato de cards apiladas. Cada card SHALL mostrar: título, badge de severidad (Info/Alerta/Urgente), badge de scope (Global/Por materia/Por cohorte/Por rol), rango de vigencia, y counter de acknowledgment "X/Y confirmaron lectura". Los avisos de severidad Urgente SHALL tener fondo destacado en rojo suave.

#### Scenario: Lista visible con avisos activos
- **WHEN** un COORDINADOR navega a `/coordinacion/avisos`
- **THEN** ve la lista de avisos con sus badges de severidad y scope

#### Scenario: Aviso urgente destacado visualmente
- **WHEN** un aviso tiene severidad "Urgente"
- **THEN** su card tiene fondo rojo suave que lo diferencia del resto

#### Scenario: Counter de acknowledgment
- **WHEN** se muestra la card de un aviso con `requiere_ack: true`
- **THEN** se muestra el texto "X de Y confirmaron lectura" con los números reales

### Requirement: Publicar aviso institucional
El sistema SHALL permitir crear un aviso desde un Drawer lateral con los siguientes campos: título (texto), cuerpo (textarea), severidad (radio buttons: Info/Alerta/Urgente), scope (dropdown: Global/Por materia/Por cohorte/Por rol), campo condicional para materia/cohorte/rol específico según el scope seleccionado, vigencia desde/hasta (date-pickers), y toggle "Requiere confirmación de lectura".

#### Scenario: Apertura del drawer de publicación
- **WHEN** el usuario hace click en "Publicar aviso"
- **THEN** se abre el Drawer lateral con el formulario vacío

#### Scenario: Campo condicional de scope
- **WHEN** el usuario selecciona scope "Por materia"
- **THEN** aparece un select de materias del tenant; al seleccionar "Global" el campo desaparece

#### Scenario: Publicar aviso exitosamente
- **WHEN** el usuario completa el formulario (título obligatorio, severidad, scope, vigencia desde) y hace click en "Publicar"
- **THEN** el aviso se crea en el backend, el drawer se cierra y la lista se actualiza

#### Scenario: Validación: título obligatorio
- **WHEN** el usuario intenta publicar sin completar el título
- **THEN** el campo muestra error "El título es obligatorio" y no se envía la request

### Requirement: Archivar aviso
El sistema SHALL permitir archivar (soft-delete) un aviso publicado. El aviso archivado no SHALL mostrarse en la lista activa.

#### Scenario: Archivar aviso
- **WHEN** el usuario hace click en el ícono "Archivar" de un aviso
- **THEN** aparece un diálogo de confirmación; al confirmar, el aviso desaparece de la lista activa

### Requirement: Vista de avisos para destinatarios (todos los roles)
El sistema SHALL mostrar a cualquier usuario autenticado los avisos vigentes que aplican a su scope (rol, materia asignada, o global). El usuario SHALL poder confirmar la lectura (ack) en avisos con `requiere_ack: true`, lo que los oculta de su lista personal.

#### Scenario: Visualización de avisos según scope del usuario
- **WHEN** un PROFESOR navega a la sección de avisos
- **THEN** ve solo los avisos cuyo scope aplica a su rol o sus materias asignadas

#### Scenario: Confirmación de lectura (ack)
- **WHEN** el usuario hace click en "Confirmar lectura" en un aviso con `requiere_ack: true`
- **THEN** el aviso desaparece de su lista personal y el counter de acknowledgment del aviso se incrementa
