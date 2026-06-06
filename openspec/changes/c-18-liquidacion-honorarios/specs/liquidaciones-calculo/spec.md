## ADDED Requirements

### Requirement: Calcular liquidaciones del período
The system SHALL calculate monthly liquidations for all active teachers in a cohort for a given period (AAAA-MM).
The calculation follows: `Total = Base(rol, vigente al periodo) + Σ(Plus(grupo, rol) × N_comisiones_del_grupo)` (RN-21/RN-34).

#### Scenario: Calcular liquidaciones exitosamente
- **GIVEN** the tenant has configured SalarioBase and SalarioPlus entries valid for the period
- **GIVEN** the tenant has Usuario records with active Asignacion entries in the cohort
- **WHEN** a FINANZAS user sends POST to `/api/liquidaciones/calcular` with valid `cohorte_id` and `periodo`
- **THEN** the system returns 200 with a list of created/updated Liquidacion records
- **AND** each Liquidacion has `monto_base`, `monto_plus`, `total`, `es_nexo` and `excluido_por_factura` correctly calculated

#### Scenario: Calcular liquidaciones es idempotente
- **WHEN** a FINANZAS user sends POST to `/api/liquidaciones/calcular` twice with the same parameters
- **THEN** the second call returns 200 with the same results (upsert behavior via UNIQUE constraint)
- **AND** no duplicate Liquidacion records are created

#### Scenario: Docente facturante se excluye de total
- **GIVEN** a Usuario with `facturador = true` has active Asignacion entries
- **WHEN** liquidations are calculated
- **THEN** the system creates a Liquidacion for that teacher with `excluido_por_factura = true`
- **AND** the teacher is included in KPIs but excluded from the payable total per RN-35

#### Scenario: Docente sin datos bancarios no se liquida
- **GIVEN** a Usuario without CBU/banco/alias configured
- **WHEN** liquidations are calculated
- **THEN** the system skips that teacher (per RN-26)

#### Scenario: Rol NEXO se calcula separadamente pero suma al total
- **GIVEN** a Usuario with asignaciones where rol = NEXO
- **WHEN** liquidations are calculated
- **THEN** the Liquidacion has `es_nexo = true`
- **AND** the NEXO amount is included in the total per RN-36

#### Scenario: Cálculo respeta periodo de vigencia de grilla
- **GIVEN** SalarioBase has `desde=2026-01-01, hasta=2026-06-30` and SalarioBase has `desde=2026-07-01, hasta=null`
- **WHEN** calculating for period `2026-05`
- **THEN** the system uses the first entry (monto from Jan-Jun)
- **WHEN** calculating for period `2026-08`
- **THEN** the system uses the second entry (monto from Jul onwards) per RN-31

#### Scenario: Cálculo incluye todas las comisiones activas del docente
- **GIVEN** a PROFESOR with 2 active Asignacion entries in the same cohort, each with distinct comisiones
- **WHEN** liquidations are calculated
- **THEN** the system counts all comisiones and applies plus accumulation per RN-33

### Requirement: Listar y consultar liquidaciones
The system SHALL provide read access to liquidations with filtering capabilities.

#### Scenario: Listar liquidaciones con filtros
- **WHEN** a FINANZAS user sends GET to `/api/liquidaciones` with optional filters `cohorte_id`, `periodo`, `usuario_id`, `estado`
- **THEN** the system returns 200 with a paginated list of matching Liquidacion records

#### Scenario: Obtener liquidación por ID
- **WHEN** a FINANZAS user sends GET to `/api/liquidaciones/{id}` with a valid ID
- **THEN** the system returns 200 with the full Liquidacion object

#### Scenario: Obtener liquidación inexistente
- **WHEN** a FINANZAS user sends GET to `/api/liquidaciones/{id}` with a non-existent ID
- **THEN** the system returns 404 Not Found

#### Scenario: Aislamiento multi-tenant en liquidaciones
- **WHEN** two tenants each have liquidaciones
- **THEN** each tenant can only see its own liquidaciones

### Requirement: Cerrar liquidación (inmutable)
The system SHALL allow closing a liquidation, making it immutable (RN-22).

#### Scenario: Cerrar liquidación exitosamente
- **GIVEN** a Liquidacion in estado `Abierta`
- **WHEN** a FINANZAS user sends POST to `/api/liquidaciones/{id}/cerrar`
- **THEN** the system returns 200 with the Liquidacion showing `estado: "Cerrada"`
- **AND** generates an audit log entry with action `LIQUIDACION_CERRAR`

#### Scenario: Cerrar liquidación ya cerrada
- **GIVEN** a Liquidacion in estado `Cerrada`
- **WHEN** a FINANZAS user sends POST to `/api/liquidaciones/{id}/cerrar`
- **THEN** the system returns 409 Conflict with error message

#### Scenario: No se puede modificar liquidación cerrada
- **GIVEN** a Liquidacion in estado `Cerrada`
- **WHEN** a FINANZAS user tries to update its fields via PUT or PATCH
- **THEN** the system returns 409 Conflict (the endpoint does not exist for liquidaciones; if a general update were to be added, it must check estado)

#### Scenario: Acceso sin permiso liquidaciones:cerrar
- **WHEN** an authenticated user without `liquidaciones:cerrar` tries to close a liquidation
- **THEN** the system returns 403 Forbidden

### Requirement: KPIs contables
The system SHALL provide accounting KPIs distinguishing invoice vs. non-invoice universes (RN-38).

#### Scenario: Obtener KPIs del período
- **WHEN** a FINANZAS user sends GET to `/api/liquidaciones/kpis?cohorte_id=X&periodo=YYYY-MM`
- **THEN** the system returns 200 with:
  - `total_sin_factura`: sum of totals where `excluido_por_factura = false`
  - `total_con_factura`: sum of totals where `excluido_por_factura = true`
  - `total_nexo`: sum of totals where `es_nexo = true`
  - `cantidad_docentes_sin_factura`
  - `cantidad_docentes_con_factura`

### Requirement: Historial de liquidaciones cerradas
The system SHALL provide access to historical closed liquidations (F10.3).

#### Scenario: Obtener historial
- **WHEN** a FINANZAS user sends GET to `/api/liquidaciones/historial?cohorte_id=X`
- **THEN** the system returns 200 with all Liquidacion records where `estado = "Cerrada"` for the given cohorte, ordered by periodo desc
