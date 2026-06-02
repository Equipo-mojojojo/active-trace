## 1. Modelos base y metadata transversal

- [x] 1.1 Crear el modelo `Tenant` y los mixins base de persistencia (`id`, timestamps, `deleted_at`, `tenant_id`) alineados con el contrato de `tenant-root-model`
- [x] 1.2 Integrar los modelos base con la metadata SQLAlchemy existente y preparar su uso desde Alembic
- [x] 1.3 Escribir tests para UUID interno, timestamps y semántica de soft delete en modelos base

## 2. Persistencia tenant-aware

- [x] 2.1 Diseñar e implementar un repository/base helper con scope automático por `tenant_id`
- [x] 2.2 Implementar el filtrado por soft delete en lecturas normales y el borrado lógico por `deleted_at`
- [x] 2.3 Escribir tests de integración que demuestren aislamiento entre tenants y exclusión de registros soft-deleted

## 3. Cifrado de atributos sensibles

- [x] 3.1 Implementar la utilidad de cifrado/descifrado AES-256 sobre `ENCRYPTION_KEY`
- [x] 3.2 Integrar la utilidad de cifrado en la capa de persistencia base para atributos sensibles reutilizables
- [x] 3.3 Escribir tests de round-trip y aserciones de no exposición de texto plano en persistencia/logs

## 4. Migraciones y bootstrap de schema

- [x] 4.1 Crear la migración Alembic 001 para `tenant` y soporte mínimo de la capa base
- [x] 4.2 Verificar que la migración respete la convención de una migración por cambio de schema y quede desacoplada de C-03/C-04

## 5. Validación final y readiness para C-03

- [x] 5.1 Ejecutar la suite de tests de C-02 contra DB real de test y confirmar verde
- [x] 5.2 Revisar que todo query base quede tenant-scoped por defecto y documentar cualquier escape explícito necesario
- [x] 5.3 Confirmar que C-02 deja lista la base de persistencia para auth y RBAC sin implementar todavía lógica de C-03/C-04
