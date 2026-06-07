## ADDED Requirements

### Requirement: Listar hilos propios del inbox
El sistema SHALL exponer via `GET /api/inbox` los hilos de mensajes donde el usuario autenticado es destinatario, ordenados por fecha de último mensaje descendente. Cada hilo muestra el asunto del primer mensaje, el remitente, la cantidad de mensajes y si hay mensajes no leídos.

#### Scenario: Listar hilos con mensajes recibidos
- **WHEN** un usuario autenticado hace GET a `/api/inbox`
- **THEN** el sistema retorna 200 con la lista de hilos propios del tenant
- **AND** cada hilo incluye `hilo_id`, `asunto`, `remitente_id`, `total_mensajes`, `tiene_no_leidos`

#### Scenario: Inbox vacío retorna lista vacía
- **WHEN** el usuario no tiene mensajes recibidos
- **THEN** el sistema retorna 200 con lista vacía `[]`

#### Scenario: Aislamiento — solo hilos propios
- **WHEN** el usuario A y usuario B tienen mensajes separados en el mismo tenant
- **THEN** GET /api/inbox del usuario A solo retorna hilos donde A es destinatario

#### Scenario: Sin autenticación retorna 401
- **WHEN** una petición no autenticada llega a `GET /api/inbox`
- **THEN** el sistema retorna 401 Unauthorized

### Requirement: Leer mensajes de un hilo
El sistema SHALL exponer via `GET /api/inbox/{hilo_id}` todos los mensajes del hilo, ordenados cronológicamente. El acceso al hilo SHALL marcarlo como leído (`leido_at` de todos los mensajes sin leer del usuario en ese hilo).

#### Scenario: Leer hilo exitosamente
- **WHEN** un usuario hace GET a `/api/inbox/{hilo_id}` siendo destinatario
- **THEN** el sistema retorna 200 con la lista de mensajes del hilo ordenados por `created_at ASC`
- **AND** todos los mensajes del hilo sin `leido_at` del usuario se marcan como leídos

#### Scenario: Acceder a hilo ajeno retorna 403
- **WHEN** un usuario intenta acceder a un hilo donde NO es ni remitente ni destinatario
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: hilo_id inexistente retorna 404
- **WHEN** el `hilo_id` no existe en el tenant
- **THEN** el sistema retorna 404 Not Found

### Requirement: Responder dentro de un hilo
El sistema SHALL permitir a cualquier participante de un hilo (remitente o destinatario) agregar un mensaje de respuesta via `POST /api/inbox/{hilo_id}/responder`.

#### Scenario: Responder en hilo propio exitosamente
- **WHEN** un participante hace POST a `/api/inbox/{hilo_id}/responder` con `{"cuerpo": "texto"}`
- **THEN** el sistema crea un nuevo `MensajeInterno` en el mismo hilo con `remitente_id = current_user.id`
- **AND** retorna 201 Created con el mensaje creado

#### Scenario: No participante no puede responder
- **WHEN** un usuario que no es parte del hilo intenta responder
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Iniciar nuevo hilo
El sistema SHALL permitir a cualquier usuario autenticado iniciar un hilo nuevo hacia otro usuario del mismo tenant via `POST /api/inbox`.

#### Scenario: Iniciar hilo exitosamente
- **WHEN** un usuario hace POST a `/api/inbox` con `{"destinatario_id": uuid, "asunto": "...", "cuerpo": "..."}`
- **THEN** el sistema crea un nuevo `MensajeInterno` con un `hilo_id` generado y retorna 201 Created

#### Scenario: Destinatario de otro tenant retorna 404
- **WHEN** el `destinatario_id` no pertenece al mismo tenant que el remitente
- **THEN** el sistema retorna 404 Not Found (aislamiento multi-tenant)

#### Scenario: Iniciar hilo con uno mismo retorna 422
- **WHEN** el `destinatario_id` es igual al `remitente_id` del usuario autenticado
- **THEN** el sistema retorna 422 Unprocessable Entity
