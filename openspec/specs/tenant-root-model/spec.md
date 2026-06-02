## ADDED Requirements

### Requirement: Tenant como raíz persistente del sistema

El sistema SHALL definir una entidad persistente `Tenant` que represente a cada institución y funcione como raíz de pertenencia para el resto del modelo de datos. Toda entidad futura del dominio SHALL poder referenciar un `tenant_id` válido derivado de esta raíz.

#### Scenario: Creación de tenant
- **WHEN** se persiste una nueva institución en la base de datos
- **THEN** el sistema crea un registro `Tenant` con identidad UUID interna única
- **AND** ese registro puede ser referenciado por entidades dependientes mediante `tenant_id`

### Requirement: Mixins base con identidad y timestamps

El sistema SHALL proveer mixins base reutilizables para modelos persistentes con `id` UUID interno, `created_at`, `updated_at` y `deleted_at`, de modo que las entidades del dominio compartan las mismas convenciones de identidad, trazabilidad temporal y soft delete.

#### Scenario: Modelo hereda campos base
- **WHEN** un modelo del dominio utiliza el mixin base definido por la plataforma
- **THEN** el modelo dispone de `id`, `created_at`, `updated_at` y `deleted_at` con semántica consistente

#### Scenario: Actualización de timestamps
- **WHEN** un registro persistido se modifica
- **THEN** `updated_at` refleja la nueva fecha-hora de modificación
- **AND** `created_at` conserva la fecha-hora original de creación

### Requirement: Entidades tenant-scoped heredan pertenencia a tenant

El sistema SHALL proveer un mixin o base class para entidades tenant-scoped que obligue la presencia de `tenant_id` como referencia persistente a `Tenant`.

#### Scenario: Entidad tenant-scoped exige tenant_id
- **WHEN** se define una entidad del dominio que vive dentro de una institución
- **THEN** esa entidad incluye `tenant_id` como parte de su contrato persistente
- **AND** `tenant_id` referencia a un `Tenant` existente
