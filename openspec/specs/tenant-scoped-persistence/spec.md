## ADDED Requirements

### Requirement: Repositories con scope de tenant por defecto

El sistema SHALL aplicar filtrado automático por `tenant_id` en los repositories base, de modo que las consultas de lectura y escritura operen únicamente sobre datos del tenant activo salvo que exista una excepción explícita y controlada.

#### Scenario: Lectura queda aislada al tenant activo
- **WHEN** un repository consulta entidades tenant-scoped usando el tenant A
- **THEN** el resultado incluye solo registros con `tenant_id` del tenant A
- **AND** excluye registros pertenecientes a cualquier otro tenant

#### Scenario: Escritura conserva pertenencia al tenant activo
- **WHEN** un repository crea una entidad tenant-scoped dentro del contexto del tenant activo
- **THEN** la entidad persistida queda asociada al `tenant_id` de ese tenant

### Requirement: Filtro de soft delete por defecto

El sistema SHALL excluir por defecto de las consultas normales los registros cuyo `deleted_at` esté informado, preservando el histórico sin tratarlos como activos.

#### Scenario: Registro eliminado lógicamente no aparece en lecturas activas
- **WHEN** una entidad tenant-scoped fue marcada con `deleted_at`
- **THEN** las consultas normales del repository no la retornan como registro activo

#### Scenario: Eliminación lógica preserva el registro
- **WHEN** una operación de borrado lógico se ejecuta sobre una entidad tenant-scoped
- **THEN** el sistema informa `deleted_at` en lugar de borrar físicamente el registro
- **AND** el registro continúa existiendo para fines de auditoría o histórico

### Requirement: Aislamiento multi-tenant verificable

El sistema SHALL demostrar mediante tests de integración que los datos de un tenant nunca son visibles ni modificables desde el contexto de otro tenant.

#### Scenario: Tenant A no ve datos de tenant B
- **WHEN** existen registros equivalentes creados para los tenants A y B
- **THEN** una consulta ejecutada en el contexto del tenant A no devuelve registros del tenant B
