## Why

Con C-01 ya existe el scaffold técnico del backend, pero todavía falta el cimiento de datos que hace viable al producto: tenancy nativo, base model transversal, cifrado en reposo y persistencia con soft delete. Este change es crítico porque define las invariantes de aislamiento y seguridad sobre las que se apoyan auth, RBAC y todos los módulos de dominio posteriores.

## What Changes

- Incorporar el modelo raíz `Tenant` y un mixin transversal con `id`, `tenant_id`, `created_at`, `updated_at` y `deleted_at` para las entidades persistentes del sistema.
- Definir una estrategia de repositorios tenant-scoped por defecto, de modo que toda query quede filtrada por `tenant_id` y el aislamiento multi-tenant sea una garantía del framework de persistencia, no una convención manual.
- Agregar un helper de cifrado AES-256 para atributos sensibles en reposo (PII y secretos) con una interfaz reutilizable por repositories y modelos futuros.
- Formalizar soft delete transversal como comportamiento base de persistencia, preservando histórico y evitando borrado físico.
- Inicializar la primera migración Alembic de dominio para `tenant` y dejar establecida la convención de una migración por cambio de schema.
- Cubrir con tests las invariantes del change: aislamiento entre tenants, cifrado round-trip, timestamps base y exclusión lógica de registros soft-deleted.

## Capabilities

### New Capabilities
- `tenant-root-model`: modelo raíz `Tenant` y mixins base para identidad UUID, timestamps y pertenencia a tenant.
- `tenant-scoped-persistence`: repositories con scope automático por `tenant_id`, incluyendo aislamiento entre instituciones y soporte de soft delete.
- `encrypted-attributes`: cifrado y descifrado AES-256 de atributos sensibles en reposo sin exposición en logs.

### Modified Capabilities
- `database-connection`: la capa de persistencia base se extiende para soportar metadata de modelos, migraciones iniciales y acceso tenant-aware sobre la infraestructura creada en C-01.

## Impact

- Afecta el backend de persistencia bajo `backend/app/core/`, `backend/app/models/`, `backend/app/repositories/` y `backend/alembic/`.
- Introduce la primera migración de dominio y el primer modelo transversal del sistema.
- Prepara el terreno para C-03 (`auth-jwt-2fa`) y C-04 (`rbac-permisos-finos`), que dependen de tener tenant isolation y base models consistentes.
- Refuerza decisiones cerradas del producto: ADR-002 row-level multi-tenancy, soft delete obligatorio y cifrado AES-256 para PII.
