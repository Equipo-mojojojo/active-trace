## Context

C-07 entregó el modelo `Asignacion` (usuario ↔ rol ↔ contexto académico), su CRUD base y los tests de aislamiento multi-tenant y vigencia. No existe aún ningún endpoint orientado al flujo de negocio real: un COORDINADOR no puede configurar un equipo completo en un solo request, ni clonar entre períodos, ni modificar vigencias en bloque. Este change construye la capa de dominio de equipos sobre el modelo ya existente, sin migración de schema.

## Goals / Non-Goals

**Goals:**
- Exponer 6 endpoints bajo `/api/equipos/*` con lógica de dominio de equipos.
- Implementar operaciones de alto valor: asignación masiva, clonado entre períodos, modificación de vigencia en bloque y export.
- Registrar `ASIGNACION_MODIFICAR` en auditoría para todas las escrituras.
- Cobertura ≥80% líneas, ≥90% reglas de negocio (TDD estricto).

**Non-Goals:**
- No se crean nuevos modelos ni migraciones (usa `Asignacion` de C-07).
- No se implementa UI/frontend (eso es C-23).
- No se modifica la lógica de resolución de permisos RBAC (ya funciona desde C-04).

## Decisions

### D1 — Sin migración: usar Asignacion de C-07
**Por qué**: el modelo `Asignacion` ya tiene todos los campos necesarios (usuario_id, rol, materia_id, carrera_id, cohorte_id, comisiones, responsable_id, desde, hasta). Agregar una migración vacía solo agrega ruido al historial de Alembic.  
**Alternativa descartada**: agregar columna `equipo_id` para agrupar asignaciones → innecesario; un "equipo" se define implícitamente por `(materia_id, carrera_id, cohorte_id)`.

### D2 — EquiposService como capa de dominio
**Por qué**: las operaciones de clonar y asignación masiva requieren lógica que no pertenece ni al router ni al repositorio. El Service coordina múltiples llamadas al repositorio, valida reglas de negocio (RN-12, RN-30) y delega a `AuditService`. El router solo valida permisos y delega; el repositorio solo ejecuta queries con scope de tenant.  
**Alternativa descartada**: lógica en el router → viola la regla dura de arquitectura limpia.

### D3 — Clonado: duplicar filas con nuevas fechas
**Por qué**: RN-12 dice que clonar duplica las asignaciones vigentes del equipo origen con las fechas del período destino. La implementación más simple y auditamente correcta es `INSERT ... SELECT` con `desde`/`hasta` del request. No se tocan las asignaciones origen.  
**Consideración**: si una asignación del origen ya tiene `hasta IS NULL` (abierta), se le asigna la `hasta` del período destino. El actor que clona queda como `actor` en auditoría.

### D4 — Export como CSV en memoria
**Por qué**: el export de equipo (F4.7) es un listado plano de asignaciones con campos simples. `csv.DictWriter` de stdlib es suficiente; no se justifica una dependencia de pandas u openpyxl para esta funcionalidad.  
**Header del response**: `Content-Disposition: attachment; filename="equipo_{materia}_{cohorte}.csv"`.

### D5 — `estado_vigencia` derivado en query, no almacenado
**Por qué**: la regla dura del modelo dice que `estado_vigencia` es derivado (`Vigente` si `desde <= hoy <= hasta OR hasta IS NULL`, `Vencida` en otro caso). Se calcula con un `CASE` en la query de repositorio para evitar inconsistencias por desincronización. No se persiste.

### D6 — Asignación masiva: transacción única
**Por qué**: RN-30 implica atomicidad — o se crean todas las asignaciones del bloque o ninguna. Se ejecutan dentro de una sola transacción SQLAlchemy. En caso de unicidad violada (asignación duplicada), la transacción se revierte completa y se retorna 409 con detalle de conflictos.

## Risks / Trade-offs

- [Riesgo] Clonar un equipo grande (decenas de asignaciones) puede tardar en instancias con muchas materias → Mitigación: la operación es síncrona pero acotada por tenant; si escala se puede mover a un background task, por ahora no justificado.
- [Trade-off] Export CSV en memoria es simple pero no escala para equipos de miles de filas → aceptado para MVP; se puede cambiar a streaming si aparece el caso.
- [Riesgo] Modificar vigencia en bloque afecta TODAS las asignaciones del equipo sin preview → Mitigación: el endpoint requiere confirmación explícita (`dry_run=true` retorna el conteo afectado antes de ejecutar).

## Migration Plan

No hay migración de schema. El deploy es:
1. Merge del PR → los nuevos endpoints quedan disponibles.
2. No hay rollback de datos porque no se modifica schema.
3. Si hay rollback de código, los endpoints desaparecen sin efecto secundario (las asignaciones creadas/clonadas quedan, son datos válidos).
