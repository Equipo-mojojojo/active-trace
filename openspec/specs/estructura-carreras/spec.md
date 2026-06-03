## ADDED Requirements

### Requirement: Administrar carreras del tenant
The system SHALL provide full CRUD operations for the `Carrera` entity, scoped to the authenticated user's tenant.
`Carrera` represents an academic program (e.g., "Tecnicatura Universitaria en Programación").

#### Scenario: Crear carrera exitosamente
- **WHEN** an ADMIN sends a POST to `/api/admin/carreras` with valid `codigo` and `nombre`
- **THEN** the system returns 201 Created with the full `Carrera` object including `id`, `estado: "Activa"`, and timestamps

#### Scenario: Crear carrera con código duplicado en el mismo tenant
- **WHEN** an ADMIN sends a POST to `/api/admin/carreras` with a `codigo` that already exists for the same tenant
- **THEN** the system returns 409 Conflict with an error message indicating duplicate code

#### Scenario: Crear carrera con código duplicado en distinto tenant
- **WHEN** two different tenants each create a Carrera with the same `codigo`
- **THEN** both operations succeed (201 Created), confirming isolation per tenant

#### Scenario: Listar carreras del tenant
- **WHEN** an ADMIN sends a GET to `/api/admin/carreras`
- **THEN** the system returns 200 with a list of all non-deleted Carreras for the current tenant

#### Scenario: Listar carreras respeta aislamiento multi-tenant
- **WHEN** two tenants each have carreras and an ADMIN from tenant A lists carreras
- **THEN** the response only contains tenant A's carreras

#### Scenario: Obtener carrera por ID existente
- **WHEN** an ADMIN sends a GET to `/api/admin/carreras/{id}` with a valid ID
- **THEN** the system returns 200 with the full Carrera object

#### Scenario: Obtener carrera por ID inexistente
- **WHEN** an ADMIN sends a GET to `/api/admin/carreras/{id}` with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar carrera exitosamente
- **WHEN** an ADMIN sends a PUT to `/api/admin/carreras/{id}` with valid fields
- **THEN** the system returns 200 with the updated Carrera object

#### Scenario: Actualizar carrera a código duplicado
- **WHEN** an ADMIN sends a PUT to `/api/admin/carreras/{id}` with a `codigo` that already belongs to another carrera in the same tenant
- **THEN** the system returns 409 Conflict

#### Scenario: Soft delete carrera
- **WHEN** an ADMIN sends a DELETE to `/api/admin/carreras/{id}`
- **THEN** the system returns 204 No Content and the carrera is soft-deleted (not returned in subsequent GET list)

#### Scenario: Soft delete carrera inexistente
- **WHEN** an ADMIN sends a DELETE to `/api/admin/carreras/{id}` with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar estado de carrera a Inactiva
- **WHEN** an ADMIN sends a PUT to `/api/admin/carreras/{id}` with `estado: "Inactiva"`
- **THEN** the system returns 200 with the carrera showing `estado: "Inactiva"`

### Requirement: Permisos de acceso a carreras
All carrera endpoints SHALL be protected by the `estructura:gestionar` permission.

#### Scenario: Acceso sin autenticación a carreras
- **WHEN** an unauthenticated request is sent to any `/api/admin/carreras` endpoint
- **THEN** the system returns 401 Unauthorized

#### Scenario: Acceso sin permiso estructura:gestionar
- **WHEN** an authenticated user without `estructura:gestionar` permission sends a request to any `/api/admin/carreras` endpoint
- **THEN** the system returns 403 Forbidden
