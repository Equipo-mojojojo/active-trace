## Context

`foundation-setup` dejó listo el backend FastAPI, la conexión async a PostgreSQL, Alembic y el scaffold por capas. El siguiente paso crítico es convertir esa base técnica en una capa de persistencia segura y multi-tenant por diseño: un `Tenant` raíz, modelos base reutilizables, repositories con scope automático, cifrado AES-256 para datos sensibles y soft delete transversal. Este change condiciona directamente C-03 y C-04, porque auth y RBAC dependen de una identidad persistida y de un aislamiento de tenant imposible de violar por accidente.

Además, el contrato del producto ya cerró ADR-002 en favor de **row-level por columna `tenant_id` + filtro automático en repositories**, por lo que C-02 no debe reabrir esa decisión: debe materializarla en código, migraciones y tests.

## Goals / Non-Goals

**Goals:**
- Introducir el modelo raíz `Tenant` y mixins base reutilizables para UUID, timestamps y soft delete.
- Definir la infraestructura de repositories tenant-aware para que el scope de tenant sea default y fail-closed.
- Incorporar un helper de cifrado AES-256 reutilizable para atributos sensibles en reposo.
- Inicializar la primera migración Alembic de dominio (`tenant`) y dejar lista la convención para cambios posteriores.
- Cubrir con tests de integración las invariantes críticas: aislamiento multi-tenant, cifrado round-trip, timestamps y soft delete.

**Non-Goals:**
- Implementar autenticación, tokens o hashing de passwords (C-03).
- Implementar catálogo de roles, permisos o guards de autorización (C-04).
- Modelar entidades de negocio posteriores como `Usuario`, `Asignacion`, `Carrera` o `Materia` fuera de lo necesario para la base transversal.
- Resolver rotación avanzada de claves o KMS externo; en C-02 alcanza con un helper consistente sobre `ENCRYPTION_KEY`.

## Decisions

### D1 — `Tenant` como único agregado raíz transversal

Se crea un modelo `Tenant` explícito y un conjunto de mixins base para que toda entidad futura herede la misma semántica: `id` UUID interno, `tenant_id`, `created_at`, `updated_at` y `deleted_at`.

**Por qué:** evita divergencias entre modelos futuros y encapsula desde el comienzo las invariantes de identidad interna, pertenencia a tenant y borrado lógico.

**Alternativa descartada:** agregar `tenant_id` manualmente modelo por modelo. Se descarta porque haría fácil olvidar campos o semánticas comunes y rompería la consistencia del dominio base.

### D2 — Tenant scoping en repositories, no en routers/services

El filtrado por `tenant_id` se centraliza en repositories y utilidades base de persistencia. Los services y routers nunca deberán “recordar” agregar el filtro manualmente.

**Por qué:** el aislamiento multi-tenant es una garantía de infraestructura, no una convención humana. Si el filtro depende de cada caso de uso, tarde o temprano habrá fugas.

**Alternativa descartada:** confiar solo en convenciones de servicio o helpers ad hoc. Se descarta por inseguro y porque contradice la regla dura del repo.

### D3 — Soft delete transversal con `deleted_at`

La eliminación lógica se implementa como timestamp nullable (`deleted_at`) y los repositories base excluyen esos registros por defecto, salvo consultas explícitas de auditoría o administración.

**Por qué:** el producto exige histórico persistente y evita hard delete en todo el dominio.

**Alternativa descartada:** flag booleano `is_deleted`. Se descarta porque pierde información temporal útil para auditoría y debugging.

### D4 — Cifrado AES-256 encapsulado en un helper de infraestructura

El cifrado de atributos sensibles se materializa en un helper centralizado de `core/security` o módulo equivalente de infraestructura base, usando `ENCRYPTION_KEY` como secreto del entorno y una API simple de `encrypt/decrypt`.

**Por qué:** concentra una responsabilidad sensible, reduce duplicación y deja un punto único para endurecer manejo de errores, serialización y futuras rotaciones de clave.

**Alternativa descartada:** cifrar campo por campo en cada repository. Se descarta por propenso a inconsistencias y exposición accidental en logs.

### D5 — Primera migración de dominio mínima y estable

La primera migración crea `tenant` y cualquier soporte mínimo imprescindible para los mixins base, sin adelantar tablas de C-03/C-04. La convención de Alembic queda explícita: una migración por cambio de schema, nombres consistentes y sin mezclar cambios no relacionados.

**Por qué:** mantiene el historial de migraciones limpio y evita que C-02 invada dominios siguientes.

**Alternativa descartada:** crear ahora tablas de auth o roles “para adelantar”. Se descarta porque rompe el orden del roadmap y mezcla concerns críticos.

## Risks / Trade-offs

- **[Riesgo: el repository base queda demasiado genérico]** → Mitigación: limitar C-02 a operaciones e invariantes realmente transversales (tenant scope, soft delete, timestamps) y dejar lógica específica para repositories concretos.
- **[Riesgo: cifrado en reposo complejo de testear y depurar]** → Mitigación: tests explícitos de round-trip y aserciones de que el valor persistido no coincide con el texto plano.
- **[Riesgo: migración inicial condiciona todo el modelo posterior]** → Mitigación: mantener la migración 001 mínima, enfocada solo en `tenant` y la infraestructura base.
- **[Trade-off: filtros automáticos de soft delete/tenant reducen flexibilidad ad hoc]** → Mitigación: proveer escapes explícitos y auditables para casos administrativos, en lugar de queries libres.

## Migration Plan

1. Crear el modelo `Tenant` y los mixins base.
2. Añadir la infraestructura tenant-aware de repositories y el helper de cifrado.
3. Generar la migración Alembic `001` para `tenant` y soporte asociado.
4. Ejecutar tests de integración sobre DB real de test validando aislamiento, soft delete y cifrado.
5. Usar esta base como prerrequisito para C-03 y C-04.

**Rollback:** revertir la migración `001` y retirar los módulos base añadidos. Como sigue siendo una etapa temprana del producto, el rollback es manejable mientras no existan datos de negocio aguas arriba.

## Open Questions

- ¿El helper de cifrado se implementará ya con versionado de payload para soportar rotación futura de claves, o se deja esa compatibilidad para un refactor posterior?
- ¿Conviene exponer desde C-02 un base repository genérico completo o solo primitivas mínimas de scoping/soft delete para evitar sobre-generalización temprana?
