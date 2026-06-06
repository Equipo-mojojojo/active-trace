## ADDED Requirements

### Requirement: El preview renderiza la plantilla con variables de sustitución sin persistir datos
`POST /api/v1/comunicaciones/preview` SHALL aceptar una plantilla de asunto y cuerpo con variables `{nombre_alumno}`, `{materia}`, `{docente}` y retornar el texto renderizado para un destinatario de ejemplo, sin crear ninguna fila en la tabla `comunicacion`.

#### Scenario: Preview renderiza variables correctamente
- **WHEN** se envía `asunto = "Hola {nombre_alumno}"` con `nombre_alumno = "Ana García"`
- **THEN** el response contiene `asunto_renderizado = "Hola Ana García"` y no se crea ninguna `Comunicacion`

#### Scenario: Preview con variable desconocida retorna error claro
- **WHEN** la plantilla contiene `{variable_inexistente}`
- **THEN** el sistema retorna `422` con mensaje indicando la variable no reconocida

#### Scenario: Preview no requiere destinatarios reales
- **WHEN** se llama al endpoint de preview sin lista de destinatarios
- **THEN** el sistema renderiza con datos de ejemplo y retorna `200`

### Requirement: El preview es obligatorio antes de encolar mensajes
El sistema SHALL rechazar solicitudes de envío que no hayan pasado por el preview en la misma sesión del usuario. El token de preview tiene una vida útil de 10 minutos.

#### Scenario: Envío sin token de preview es rechazado
- **WHEN** se llama a `POST /api/v1/comunicaciones/enviar` sin incluir un `preview_token` válido
- **THEN** el sistema retorna `422` con mensaje "Se requiere preview previo al envío"

#### Scenario: Envío con token de preview expirado es rechazado
- **WHEN** se llama a enviar con un `preview_token` de más de 10 minutos de antigüedad
- **THEN** el sistema retorna `422` con mensaje "El token de preview expiró"

#### Scenario: Envío con token de preview válido procede
- **WHEN** se llama a enviar con un `preview_token` generado en los últimos 10 minutos
- **THEN** los mensajes son encolados correctamente

### Requirement: El preview requiere permiso comunicacion:enviar
`POST /api/v1/comunicaciones/preview` SHALL requerir el permiso `comunicacion:enviar`.

#### Scenario: Usuario sin permiso es rechazado en preview
- **WHEN** un usuario sin `comunicacion:enviar` llama al endpoint de preview
- **THEN** el sistema retorna `403`
