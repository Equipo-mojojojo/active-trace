## ADDED Requirements

### Requirement: CRUD de programas de materia

El sistema SHALL permitir gestionar los programas/documentos oficiales de cada materia asociados a una combinación de carrera y cohorte.

#### Scenario: Crear programa de materia exitosamente
- **WHEN** un usuario con permiso `estructura:gestionar` envía un POST a `/api/admin/programas` con `titulo`, `materia_id`, `carrera_id`, `cohorte_id` y `referencia_archivo` válidos
- **THEN** el sistema crea el registro, asigna el `tenant_id` del usuario autenticado, establece `cargado_at` con la fecha/hora actual, y retorna 201 Created con los datos del programa

#### Scenario: Listar programas con filtros
- **WHEN** un usuario autenticado envía un GET a `/api/admin/programas` con parámetros opcionales `materia_id`, `carrera_id` y/o `cohorte_id`
- **THEN** el sistema retorna 200 OK con un array de programas que coinciden con los filtros, excluyendo registros soft-delete y limitados al tenant del usuario

#### Scenario: Obtener programa por ID
- **WHEN** un usuario autenticado envía un GET a `/api/admin/programas/{id}` con un ID existente
- **THEN** el sistema retorna 200 OK con los datos del programa

#### Scenario: Obtener programa inexistente retorna 404
- **WHEN** un usuario autenticado envía un GET a `/api/admin/programas/{id}` con un ID que no existe o fue soft-deleted
- **THEN** el sistema retorna 404 Not Found

#### Scenario: Actualizar programa
- **WHEN** un usuario con permiso `estructura:gestionar` envía un PUT a `/api/admin/programas/{id}` con campos a actualizar
- **THEN** el sistema actualiza solo los campos enviados y retorna 200 OK con los datos actualizados

#### Scenario: Eliminar programa (soft-delete)
- **WHEN** un usuario con permiso `estructura:gestionar` envía un DELETE a `/api/admin/programas/{id}`
- **THEN** el sistema marca el registro como eliminado (soft-delete) y retorna 204 No Content

#### Scenario: Aislamiento multi-tenant en programas
- **WHEN** un usuario del Tenant A crea un programa y un usuario del Tenant B lista programas
- **THEN** los programas del Tenant A no son visibles para el Tenant B

### Requirement: Validación de datos en programa de materia

El sistema SHALL validar los datos de entrada en las operaciones CRUD de programas.

#### Scenario: Crear programa sin `referencia_archivo` retorna 422
- **WHEN** un usuario envía un POST a `/api/admin/programas` sin el campo `referencia_archivo`
- **THEN** el sistema retorna 422 Unprocessable Entity con el detalle del campo faltante

#### Scenario: Actualizar programa con campos extra retorna 422
- **WHEN** un usuario envía un PUT a `/api/admin/programas/{id}` con un campo no declarado en el schema
- **THEN** el sistema retorna 422 Unprocessable Entity (por `extra="forbid"` en el schema)
