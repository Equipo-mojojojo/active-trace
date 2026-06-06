## ADDED Requirements

### Requirement: Administrar SalarioBase por rol con vigencia
El sistema SHALL permitir a FINANZAS crear, editar y listar registros de `SalarioBase` (monto por rol con vigencia `desde/hasta`) scoped al tenant. Solo puede existir un registro vigente por rol en un instante dado.

#### Scenario: Crear SalarioBase exitosamente
- **WHEN** FINANZAS hace POST a `/api/liquidaciones/salarios/base` con `rol`, `monto`, `desde` válidos
- **THEN** el sistema retorna 201 Created con el registro creado incluyendo `id` y `tenant_id`

#### Scenario: Crear SalarioBase con vigencia solapada
- **WHEN** FINANZAS intenta crear un SalarioBase para un rol que ya tiene vigencia activa en ese rango
- **THEN** el sistema retorna 409 Conflict indicando solapamiento de vigencia

#### Scenario: Listar SalarioBase del tenant
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/salarios/base`
- **THEN** el sistema retorna 200 con la lista de registros del tenant en orden cronológico

#### Scenario: Editar SalarioBase existente
- **WHEN** FINANZAS hace PUT a `/api/liquidaciones/salarios/base/{id}` con campos válidos
- **THEN** el sistema retorna 200 con el registro actualizado

#### Scenario: Aislamiento multi-tenant en SalarioBase
- **WHEN** un usuario de tenant B intenta acceder a registros de tenant A
- **THEN** el sistema retorna 404 Not Found

### Requirement: Administrar SalarioPlus por grupo × rol con vigencia
El sistema SHALL permitir a FINANZAS crear, editar y listar registros de `SalarioPlus` identificados por `(grupo, rol)` con vigencia temporal. El campo `grupo` es texto libre (ej: "PROG") — no hardcodeado.

#### Scenario: Crear SalarioPlus exitosamente
- **WHEN** FINANZAS hace POST a `/api/liquidaciones/salarios/plus` con `grupo`, `rol`, `monto`, `descripcion`, `desde` válidos
- **THEN** el sistema retorna 201 Created con el registro creado

#### Scenario: Crear SalarioPlus con vigencia solapada para mismo grupo+rol
- **WHEN** ya existe un SalarioPlus vigente para `(grupo="PROG", rol="PROFESOR")` en el mismo rango
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Listar SalarioPlus del tenant
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/salarios/plus`
- **THEN** el sistema retorna 200 con la lista de registros, opcionalmente filtrable por `grupo` y `rol`

#### Scenario: Seleccionar SalarioPlus vigente para un período
- **WHEN** el motor de cálculo busca el plus de `(grupo="PROG", rol="PROFESOR")` para el período `2026-05`
- **THEN** el sistema retorna el registro cuyo `desde <= 2026-05-01` y (`hasta` es null o `hasta >= 2026-05-31`)
- **AND** si no existe registro vigente para ese período, retorna monto 0 (sin error)

### Requirement: Permisos de la grilla salarial
Todos los endpoints de grilla salarial SHALL requerir el permiso `liquidaciones:configurar-salarios`.

#### Scenario: Acceso sin permiso liquidaciones:configurar-salarios
- **WHEN** un usuario sin `liquidaciones:configurar-salarios` accede a cualquier endpoint `/api/liquidaciones/salarios/*`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Acceso sin autenticación
- **WHEN** una petición no autenticada llega a cualquier endpoint `/api/liquidaciones/salarios/*`
- **THEN** el sistema retorna 401 Unauthorized
