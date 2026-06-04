## ADDED Requirements

### Requirement: Administrar cohortes del tenant
The system SHALL provide full CRUD operations for the `Cohorte` entity, scoped to the authenticated user's tenant.
`Cohorte` represents a cohort/class group within a `Carrera` (e.g., "MAR-2026" for the March 2026 intake).

#### Scenario: Crear cohorte exitosamente
- **WHEN** an ADMIN sends a POST to `/api/admin/cohortes` with valid `carrera_id`, `nombre`, `anio`, `vig_desde`, and `estado`
- **THEN** the system returns 201 Created with the full Cohorte object including `id`, `vig_hasta: null`, and timestamps

#### Scenario: Crear cohorte con nombre duplicado en misma carrera y tenant
- **WHEN** an ADMIN sends a POST to `/api/admin/cohortes` with a `nombre` that already exists for the same `(tenant_id, carrera_id)` combination
- **THEN** the system returns 409 Conflict with an error message indicating duplicate name

#### Scenario: Crear cohorte con mismo nombre en distinta carrera
- **WHEN** an ADMIN creates two cohortes with the same `nombre` but different `carrera_id` within the same tenant
- **THEN** both operations succeed (201 Created), confirming the uniqueness scope is per-carrera

#### Scenario: Crear cohorte con carrera inactiva y vig_hasta nulo (abierta)
- **WHEN** an ADMIN sends a POST to `/api/admin/cohortes` with `vig_hasta: null` and a `carrera_id` that belongs to an Inactiva carrera
- **THEN** the system returns 422 Unprocessable Entity explaining that inactive carreras cannot have open cohorts

#### Scenario: Crear cohorte con carrera inactiva y vig_hasta definido (cerrada)
- **WHEN** an ADMIN sends a POST to `/api/admin/cohortes` with `vig_hasta` set and a `carrera_id` that belongs to an Inactiva carrera
- **THEN** the system returns 201 Created (closed cohorts on inactive carreras are allowed)

#### Scenario: Listar cohortes del tenant
- **WHEN** an ADMIN sends a GET to `/api/admin/cohortes`
- **THEN** the system returns 200 with a list of all non-deleted Cohorte records for the current tenant

#### Scenario: Listar cohortes respeta aislamiento multi-tenant
- **WHEN** two tenants each have cohortes and an ADMIN from tenant A lists cohortes
- **THEN** the response only contains tenant A's cohortes

#### Scenario: Obtener cohorte por ID existente
- **WHEN** an ADMIN sends a GET to `/api/admin/cohortes/{id}` with a valid ID
- **THEN** the system returns 200 with the full Cohorte object including `carrera_id`

#### Scenario: Obtener cohorte por ID inexistente
- **WHEN** an ADMIN sends a GET to `/api/admin/cohortes/{id}` with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar cohorte exitosamente
- **WHEN** an ADMIN sends a PUT to `/api/admin/cohortes/{id}` with valid fields
- **THEN** the system returns 200 with the updated Cohorte object

#### Scenario: Actualizar cohorte a vig_hasta nulo cuando carrera está inactiva
- **WHEN** an ADMIN sends a PUT to `/api/admin/cohortes/{id}` setting `vig_hasta: null` while the linked carrera is Inactiva
- **THEN** the system returns 422 Unprocessable Entity

#### Scenario: Soft delete cohorte
- **WHEN** an ADMIN sends a DELETE to `/api/admin/cohortes/{id}`
- **THEN** the system returns 204 No Content and the cohorte is soft-deleted

### Requirement: Permisos de acceso a cohortes
All cohorte endpoints SHALL be protected by the `estructura:gestionar` permission.

#### Scenario: Acceso sin autenticación a cohortes
- **WHEN** an unauthenticated request is sent to any `/api/admin/cohortes` endpoint
- **THEN** the system returns 401 Unauthorized

#### Scenario: Acceso sin permiso estructura:gestionar
- **WHEN** an authenticated user without `estructura:gestionar` permission sends a request to any `/api/admin/cohortes` endpoint
- **THEN** the system returns 403 Forbidden
