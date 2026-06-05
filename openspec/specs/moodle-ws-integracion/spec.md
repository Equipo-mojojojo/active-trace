## ADDED Requirements

### Requirement: Cliente Moodle WS encapsula la comunicación con el LMS
El sistema SHALL exponer un cliente `integrations/moodle_ws.py` con métodos `get_enrolled_users(course_id)` y `get_course_activities(course_id)` que consuman los Moodle Web Services. Si `MOODLE_URL` o `MOODLE_TOKEN` no están configurados, el cliente SHALL lanzar `MoodleNotConfiguredError`.

#### Scenario: Cliente retorna participantes del curso correctamente
- **WHEN** se llama `get_enrolled_users` con credenciales válidas y un course_id existente
- **THEN** el método retorna una lista de dicts con los campos esperados (nombre, apellido, email)

#### Scenario: Error de red del LMS lanza MoodleWSError
- **WHEN** el LMS no responde dentro del timeout configurado (default 30s)
- **THEN** el cliente lanza `MoodleWSError` con el detalle del error

#### Scenario: LMS sin configurar retorna error descriptivo
- **WHEN** `MOODLE_URL` o `MOODLE_TOKEN` no están en las variables de entorno
- **THEN** el cliente lanza `MoodleNotConfiguredError` con mensaje claro

### Requirement: Sync on-demand de participantes desde Moodle
El sistema SHALL exponer `POST /api/padron/sync-moodle` que tome `materia_id`, `cohorte_id` y `moodle_course_id`, consulte el LMS y cree/actualice la versión activa del padrón. Si el LMS falla, retorna `502`. Si el LMS no está configurado, retorna `503`. Requiere `padron:importar`.

#### Scenario: Sync exitosa crea nueva versión activa del padrón
- **WHEN** la integración Moodle responde correctamente con 20 alumnos
- **THEN** el sistema crea una nueva `VersionPadron` activa con 20 `EntradaPadron` y retorna `201 Created`

#### Scenario: Error del LMS retorna 502 con mensaje de reintento
- **WHEN** el LMS responde con error o timeout
- **THEN** el sistema retorna `502 Bad Gateway` con `detail: "Error al conectar con el LMS. Reintentá en unos minutos o importá el padrón manualmente."`

#### Scenario: LMS no configurado retorna 503
- **WHEN** `MOODLE_URL` o `MOODLE_TOKEN` no están configurados para el tenant
- **THEN** el sistema retorna `503 Service Unavailable` con mensaje sobre fallback manual

### Requirement: Sync nocturna invocable por el worker
El sistema SHALL exponer un método `PadronService.sync_nocturna_all_tenants()` que pueda ser llamado por el worker para sincronizar todos los padrones configurados con Moodle. Los errores por tenant son aislados — un fallo en un tenant no interrumpe la sync de los demás.

#### Scenario: Sync nocturna procesa todos los tenants independientemente
- **WHEN** hay 3 tenants configurados y el Moodle del tenant 2 falla
- **THEN** el sistema procesa correctamente el tenant 1 y el tenant 3, registra el error del tenant 2 en logs estructurados, y retorna un resumen con éxitos y fallos por tenant
