## ADDED Requirements

### Requirement: El sistema SHALL almacenar roles como datos administrables
El sistema SHALL persistir la definición de roles en una tabla `rol` con los siguientes campos:
- `id`: UUID primary key
- `tenant_id`: UUID foreign key a `tenant`, NOT NULL
- `nombre`: string (255), único por tenant, NOT NULL
- `descripcion`: string (255), nullable
- `editable`: booleano, default TRUE (roles del sistema como ADMIN pueden ser no editables)
- `created_at`, `updated_at`, `deleted_at` (soft delete)

#### Scenario: Creación de rol
- **WHEN** un usuario con permiso `rbac:gestionar` crea un rol
- **THEN** el sistema persiste el rol con id, tenant_id, nombre y descripción

#### Scenario: Unicidad de nombre por tenant
- **WHEN** se intenta crear un rol con un nombre que ya existe en el mismo tenant
- **THEN** el sistema rechaza la operación con error de unicidad

#### Scenario: Soft delete de rol
- **WHEN** se elimina un rol
- **THEN** el sistema marca deleted_at sin borrar el registro físico

### Requirement: El sistema SHALL almacenar permisos como catálogo administrable
El sistema SHALL persistir el catálogo de permisos en una tabla `permiso` con los siguientes campos:
- `id`: UUID primary key
- `tenant_id`: UUID foreign key a `tenant`, NOT NULL
- `codigo`: string (100), único por tenant, NOT NULL (formato `modulo:accion` o `modulo:accion:propio`)
- `modulo`: string (50), NOT NULL
- `accion`: string (50), NOT NULL
- `descripcion`: string (255), nullable

#### Scenario: Creación de permiso
- **WHEN** un usuario administrador crea un permiso con código `calificaciones:importar`
- **THEN** el sistema persiste el permiso con modulo="calificaciones", accion="importar"

#### Scenario: Unicidad de código por tenant
- **WHEN** se intenta crear un permiso con un código duplicado en el mismo tenant
- **THEN** el sistema rechaza la operación con error de unicidad

### Requirement: El sistema SHALL relacionar roles y permisos mediante tabla asociativa
El sistema SHALL persistir la matriz rol × permiso en una tabla `rol_permiso` con primary key compuesta `(rol_id, permiso_id, tenant_id)`.

#### Scenario: Asignación de permiso a rol
- **WHEN** un administrador asigna el permiso `calificaciones:importar` al rol PROFESOR
- **THEN** el sistema crea un registro en `rol_permiso` vinculando ambos

#### Scenario: Prevención de duplicados
- **WHEN** se intenta asignar el mismo permiso a un rol que ya lo tiene
- **THEN** el sistema rechaza la operación (unique constraint)

### Requirement: El sistema SHALL sembrar la matriz de capacidades inicial mediante migración
La migración 002 SHALL crear los 7 roles del dominio y asignar los permisos según la matriz documentada en `knowledge-base/03_actores_y_roles.md §3.3`.

#### Scenario: Seed de roles
- **WHEN** se ejecuta la migración 002
- **THEN** existen los roles ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS

#### Scenario: Seed de permisos
- **WHEN** se ejecuta la migración 002
- **THEN** existen los permisos documentados en la matriz (aprox. 30-35) con sus códigos correspondientes

#### Scenario: Seed de asignaciones rol-permiso
- **WHEN** se ejecuta la migración 002
- **THEN** cada rol tiene exactamente los permisos especificados en la matriz de capacidades

### Requirement: El modelo SHALL heredar de TenantScopedModelMixin
Todas las tablas (rol, permiso, rol_permiso) SHALL heredar de `TenantScopedModelMixin` para garantizar aislamiento multi-tenant row-level.

#### Scenario: Aislamiento por tenant
- **WHEN** se consultan roles desde el tenant A
- **THEN** NO se retornan roles del tenant B

### Requirement: El sistema SHALL resolver permisos efectivos como unión de roles del usuario
El sistema SHALL proveer una función `get_effective_permissions(user_id, tenant_id)` que retorne el conjunto de códigos de permiso resultante de la unión de todos los roles del usuario.

#### Scenario: Unión de permisos multi-rol
- **WHEN** un usuario tiene los roles PROFESOR y COORDINADOR
- **THEN** sus permisos efectivos son la unión de los permisos de ambos roles
