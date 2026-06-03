## ADDED Requirements

### Requirement: Administrar materias del tenant
The system SHALL provide full CRUD operations for the `Materia` entity, scoped to the authenticated user's tenant.
`Materia` is the tenant-wide subject catalog (e.g., "Programación I" with code "PROG_I"). Per ADR-006, this is a unique catalog; instance-level data (Dictado) comes in a later change.

#### Scenario: Crear materia exitosamente
- **WHEN** an ADMIN sends a POST to `/api/admin/materias` with valid `codigo` and `nombre`
- **THEN** the system returns 201 Created with the full Materia object including `id`, `estado: "Activa"`, and timestamps

#### Scenario: Crear materia con código duplicado en el mismo tenant
- **WHEN** an ADMIN sends a POST to `/api/admin/materias` with a `codigo` that already exists for the same tenant
- **THEN** the system returns 409 Conflict with an error message indicating duplicate code

#### Scenario: Crear materia con código duplicado en distinto tenant
- **WHEN** two different tenants each create a Materia with the same `codigo`
- **THEN** both operations succeed (201 Created), confirming isolation per tenant

#### Scenario: Listar materias del tenant
- **WHEN** an ADMIN sends a GET to `/api/admin/materias`
- **THEN** the system returns 200 with a list of all non-deleted Materias for the current tenant

#### Scenario: Listar materias respeta aislamiento multi-tenant
- **WHEN** two tenants each have materias and an ADMIN from tenant A lists materias
- **THEN** the response only contains tenant A's materias

#### Scenario: Obtener materia por ID existente
- **WHEN** an ADMIN sends a GET to `/api/admin/materias/{id}` with a valid ID
- **THEN** the system returns 200 with the full Materia object

#### Scenario: Obtener materia por ID inexistente
- **WHEN** an ADMIN sends a GET to `/api/admin/materias/{id}` with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar materia exitosamente
- **WHEN** an ADMIN sends a PUT to `/api/admin/materias/{id}` with valid fields
- **THEN** the system returns 200 with the updated Materia object

#### Scenario: Soft delete materia
- **WHEN** an ADMIN sends a DELETE to `/api/admin/materias/{id}`
- **THEN** the system returns 204 No Content and the materia is soft-deleted

### Requirement: Permisos de acceso a materias
All materia endpoints SHALL be protected by the `estructura:gestionar` permission.

#### Scenario: Acceso sin autenticación a materias
- **WHEN** an unauthenticated request is sent to any `/api/admin/materias` endpoint
- **THEN** the system returns 401 Unauthorized

#### Scenario: Acceso sin permiso estructura:gestionar
- **WHEN** an authenticated user without `estructura:gestionar` permission sends a request to any `/api/admin/materias` endpoint
- **THEN** the system returns 403 Forbidden
