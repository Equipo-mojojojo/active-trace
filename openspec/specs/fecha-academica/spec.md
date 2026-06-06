## ADDED Requirements

### Requirement: CRUD de fechas académicas

El sistema SHALL permitir gestionar la calendarización de instancias evaluativas (parciales, trabajos prácticos, coloquios, recuperatorios) por materia, cohorte y número de instancia.

#### Scenario: Crear fecha académica exitosamente
- **WHEN** un usuario con permiso `estructura:gestionar` envía un POST a `/api/admin/fechas-academicas` con `materia_id`, `cohorte_id`, `tipo`, `numero`, `periodo`, `fecha` y `titulo` válidos
- **THEN** el sistema crea el registro con el `tenant_id` del usuario autenticado y retorna 201 Created con los datos de la fecha académica

#### Scenario: Listar fechas académicas con filtros
- **WHEN** un usuario autenticado envía un GET a `/api/admin/fechas-academicas` con parámetros opcionales `materia_id`, `cohorte_id` y/o `tipo`
- **THEN** el sistema retorna 200 OK con un array de fechas que coinciden con los filtros, excluyendo registros soft-delete y limitados al tenant del usuario

#### Scenario: Obtener fecha académica por ID
- **WHEN** un usuario autenticado envía un GET a `/api/admin/fechas-academicas/{id}` con un ID existente
- **THEN** el sistema retorna 200 OK con los datos de la fecha académica

#### Scenario: Obtener fecha académica inexistente retorna 404
- **WHEN** un usuario autenticado envía un GET a `/api/admin/fechas-academicas/{id}` con un ID que no existe o fue soft-deleted
- **THEN** el sistema retorna 404 Not Found

#### Scenario: Actualizar fecha académica
- **WHEN** un usuario con permiso `estructura:gestionar` envía un PUT a `/api/admin/fechas-academicas/{id}` con campos a actualizar
- **THEN** el sistema actualiza solo los campos enviados y retorna 200 OK con los datos actualizados

#### Scenario: Eliminar fecha académica (soft-delete)
- **WHEN** un usuario con permiso `estructura:gestionar` envía un DELETE a `/api/admin/fechas-academicas/{id}`
- **THEN** el sistema marca el registro como eliminado (soft-delete) y retorna 204 No Content

#### Scenario: Aislamiento multi-tenant en fechas académicas
- **WHEN** un usuario del Tenant A crea una fecha académica y un usuario del Tenant B lista fechas académicas
- **THEN** las fechas del Tenant A no son visibles para el Tenant B

### Requirement: Validación de datos en fecha académica

El sistema SHALL validar los datos de entrada en las operaciones CRUD de fechas académicas.

#### Scenario: Crear fecha con tipo inválido retorna 422
- **WHEN** un usuario envía un POST a `/api/admin/fechas-academicas` con un `tipo` que no está en el enum `TipoEvaluacion`
- **THEN** el sistema retorna 422 Unprocessable Entity con el detalle de validación

#### Scenario: Actualizar fecha académica con campos extra retorna 422
- **WHEN** un usuario envía un PUT a `/api/admin/fechas-academicas/{id}` con un campo no declarado en el schema
- **THEN** el sistema retorna 422 Unprocessable Entity (por `extra="forbid"` en el schema)

### Requirement: Fechas académicas con `cargado_at` automático

No corresponde — este requirement es para `ProgramaMateria`. Las fechas académicas no tienen `cargado_at`.
