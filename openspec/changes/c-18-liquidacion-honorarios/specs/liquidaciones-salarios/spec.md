## ADDED Requirements

### Requirement: Administrar grupos de materias (catálogo)
The system SHALL provide CRUD operations for `GrupoMateria`, scoped to the authenticated user's tenant.
`GrupoMateria` defines subject group keys (e.g., "PROG", "BD", "ING", "MAT") that are used to categorize subjects for salary plus calculation.

#### Scenario: Crear grupo de materia exitosamente
- **GIVEN** the user has `liquidaciones:configurar-salarios` permission
- **WHEN** the user sends a POST to `/api/admin/grupos-materia` with valid `clave` and `descripcion`
- **THEN** the system returns 201 Created with the full GrupoMateria object

#### Scenario: Crear grupo con clave duplicada en el mismo tenant
- **GIVEN** an existing GrupoMateria with `clave=PROG`
- **WHEN** the user sends a POST with `clave=PROG`
- **THEN** the system returns 409 Conflict

#### Scenario: Listar grupos del tenant
- **WHEN** the user sends a GET to `/api/admin/grupos-materia`
- **THEN** the system returns 200 with all GrupoMateria entries for the current tenant

#### Scenario: Aislamiento multi-tenant
- **WHEN** two tenants each create GrupoMateria entries with the same clave
- **THEN** both succeed (isolation) and each tenant only sees its own entries

### Requirement: Administrar salario base por rol
The system SHALL provide full CRUD operations for `SalarioBase`, scoped to the authenticated user's tenant.
`SalarioBase` defines the base monthly salary amount per role (PROFESOR, TUTOR, NEXO, COORDINADOR) with temporal validity.

#### Scenario: Crear salario base exitosamente
- **GIVEN** the user has `liquidaciones:configurar-salarios` permission
- **WHEN** the user sends a POST to `/api/liquidaciones/salarios-base` with valid `rol`, `monto`, `desde` and optional `hasta`
- **THEN** the system returns 201 Created with the full `SalarioBase` object including `id` and timestamps

#### Scenario: Crear salario base con solapamiento de vigencia
- **GIVEN** an existing SalarioBase for rol=PROFESOR with `desde=2026-01-01` and `hasta=null`
- **WHEN** the user sends a POST with rol=PROFESOR and `desde=2026-06-01`
- **THEN** the system returns 409 Conflict because there is already an active entry for that rol (overlapping validity is not allowed per RN-31)

#### Scenario: Crear salario base para rol inexistente
- **WHEN** the user sends a POST with an invalid rol value
- **THEN** the system returns 422 Unprocessable Entity

#### Scenario: Listar salarios base del tenant
- **WHEN** the user sends a GET to `/api/liquidaciones/salarios-base`
- **THEN** the system returns 200 with a list of all non-deleted SalarioBase entries for the current tenant

#### Scenario: Obtener salario base por ID
- **WHEN** the user sends a GET to `/api/liquidaciones/salarios-base/{id}` with a valid ID
- **THEN** the system returns 200 with the full SalarioBase object
- **WHEN** the user sends a GET with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar salario base
- **WHEN** the user sends a PUT to `/api/liquidaciones/salarios-base/{id}` with valid fields
- **THEN** the system returns 200 with the updated SalarioBase object

#### Scenario: Soft delete salario base
- **WHEN** the user sends a DELETE to `/api/liquidaciones/salarios-base/{id}`
- **THEN** the system returns 204 No Content and the entry is soft-deleted

#### Scenario: Aislamiento multi-tenant en salarios base
- **WHEN** two tenants each create SalarioBase entries
- **THEN** each tenant can only see and manage its own entries

### Requirement: Administrar plus salarial por grupo y rol
The system SHALL provide full CRUD operations for `SalarioPlus`, scoped to the authenticated user's tenant.
`SalarioPlus` defines additional pay per subject group (FK to `GrupoMateria`) and role with temporal validity.

#### Scenario: Crear plus salarial exitosamente
- **GIVEN** the user has `liquidaciones:configurar-salarios` permission
- **AND** a GrupoMateria with `clave=PROG` exists
- **WHEN** the user sends a POST to `/api/liquidaciones/salarios-plus` with valid `grupo_id`, `rol`, `monto`, `descripcion`, `desde` and optional `hasta`
- **THEN** the system returns 201 Created

#### Scenario: Crear plus salarial con solapamiento
- **GIVEN** an existing SalarioPlus for (grupo_id=<id_PROG>, rol=PROFESOR) with `desde=2026-01-01` and `hasta=null`
- **WHEN** the user sends a POST with the same (grupo_id=<id_PROG>, rol=PROFESOR) and `desde=2026-03-01`
- **THEN** the system returns 409 Conflict (overlapping validity)

#### Scenario: Listar plus del tenant
- **WHEN** the user sends a GET to `/api/liquidaciones/salarios-plus`
- **THEN** the system returns 200 with all non-deleted SalarioPlus entries

#### Scenario: Soft delete plus salarial
- **WHEN** the user sends a DELETE to `/api/liquidaciones/salarios-plus/{id}`
- **THEN** the system returns 204 No Content and the entry is soft-deleted

### Requirement: Control de acceso a grilla salarial
All salary grid endpoints SHALL be protected by the `liquidaciones:configurar-salarios` permission.

#### Scenario: Acceso sin autenticación
- **WHEN** an unauthenticated request is sent to any `/api/liquidaciones/salarios-base` or `/api/liquidaciones/salarios-plus` endpoint
- **THEN** the system returns 401 Unauthorized

#### Scenario: Acceso sin permiso
- **WHEN** an authenticated user without `liquidaciones:configurar-salarios` sends a request
- **THEN** the system returns 403 Forbidden
