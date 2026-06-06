## ADDED Requirements

### Requirement: Administrar facturas de docentes facturantes
The system SHALL provide CRUD operations for `Factura`, scoped to the authenticated user's tenant.
`Factura` represents an invoice submitted by teachers who work under independent billing (monotributo), per RN-35/RN-39/RN-40.

#### Scenario: Crear factura exitosamente
- **GIVEN** the user has `facturas:gestionar` permission
- **GIVEN** the referenced Usuario has `facturador = true`
- **WHEN** the user sends a POST to `/api/facturas` with valid `usuario_id`, `periodo`, `detalle`, `referencia_archivo`, `tamano_kb`
- **THEN** the system returns 201 Created with the full Factura object including `estado: "Pendiente"` and `cargada_at` timestamp

#### Scenario: Crear factura para docente no facturante
- **WHEN** the user sends a POST to `/api/facturas` with a `usuario_id` where `facturador = false`
- **THEN** the system returns 422 Unprocessable Entity

#### Scenario: Listar facturas con filtros
- **WHEN** the user sends a GET to `/api/facturas` with optional filters `usuario_id`, `periodo`, `estado`
- **THEN** the system returns 200 with a list of matching Factura records

#### Scenario: Obtener factura por ID
- **WHEN** the user sends a GET to `/api/facturas/{id}` with a valid ID
- **THEN** the system returns 200 with the full Factura object
- **WHEN** the user sends a GET with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Actualizar factura pendiente
- **GIVEN** a Factura in estado `Pendiente`
- **WHEN** the user sends a PUT to `/api/facturas/{id}` with valid fields
- **THEN** the system returns 200 with the updated Factura object

#### Scenario: No se puede actualizar factura abonada
- **GIVEN** a Factura in estado `Abonada`
- **WHEN** the user sends a PUT to `/api/facturas/{id}`
- **THEN** the system returns 409 Conflict

#### Scenario: No se puede eliminar una factura
- **WHEN** the user sends a DELETE to `/api/facturas/{id}`
- **THEN** the system returns 405 Method Not Allowed (facturas are financial records that cannot be deleted, per design decision D5)

### Requirement: Marcar factura como abonada
The system SHALL allow changing a factura's estado to "Abonada" (RN-39).

#### Scenario: Abonar factura exitosamente
- **GIVEN** a Factura in estado `Pendiente`
- **WHEN** the user sends a POST to `/api/facturas/{id}/abonar`
- **THEN** the system returns 200 with the Factura showing `estado: "Abonada"` and `abonada_at` timestamp

#### Scenario: Abonar factura ya abonada
- **GIVEN** a Factura in estado `Abonada`
- **WHEN** the user sends a POST to `/api/facturas/{id}/abonar`
- **THEN** the system returns 409 Conflict

### Requirement: Control de acceso a facturas
All factura endpoints SHALL be protected by the `facturas:gestionar` permission.

#### Scenario: Acceso sin autenticación
- **WHEN** an unauthenticated request is sent to any `/api/facturas` endpoint
- **THEN** the system returns 401 Unauthorized

#### Scenario: Acceso sin permiso facturas:gestionar
- **WHEN** an authenticated user without `facturas:gestionar` sends a request
- **THEN** the system returns 403 Forbidden

#### Scenario: Aislamiento multi-tenant en facturas
- **WHEN** two tenants each create Factura records
- **THEN** each tenant can only see and manage its own facturas
