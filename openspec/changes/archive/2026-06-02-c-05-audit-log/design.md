## Context

El sistema carece de registro de auditoría. Toda acción significativa debe quedar registrada en un log inmutable (append-only) que permita trazabilidad completa: quién hizo qué, cuándo, sobre qué recurso, desde dónde, y con qué resultado.

C-04 ya definió los permisos `auditoria:ver` (ADMIN, COORDINADOR global, COORDINADOR `:propio`) e `impersonacion:usar` (ADMIN). Este cambio implementa el modelo de datos, el servicio, el middleware de captura de contexto, la API de consulta, y el mecanismo de impersonación.

## Goals / Non-Goals

**Goals:**
- Modelo `AuditLog` append-only con trigger DB que rechaza UPDATE/DELETE
- `AuditService` para registrar acciones con códigos estandarizados
- `AuditMiddleware` que captura IP y user_agent por request y los inyecta como `RequestContext` vía `request.state`
- API `GET /api/admin/audit-log` con filtros (fechas, actor, materia, código de acción)
- Endpoints de impersonación: iniciar (`POST /api/admin/impersonacion/iniciar`) y finalizar (`POST /api/admin/impersonacion/finalizar`)
- Sesión distinguible bajo impersonación: claim `es_impersonacion: true` en JWT access
- Toda acción bajo impersonación se atribuye al actor real (actor_id en AuditLog)
- Protección con `require_permission("auditoria:ver")` e `require_permission("impersonacion:usar")`
- Migración Alembic 0004 con la tabla + trigger + seed de códigos de acción

**Non-Goals:**
- **No** incluye el panel de métricas F9.1 (gráficos, dashboard) — eso va en C-19
- **No** incluye la integración del AuditService en los módulos de dominio (C-08 en adelante) — cada change llamará al AuditService cuando corresponda
- **No** incluye retención/configuración de purge del log — el log es permanente

## Decisions

### D1 — Append-only vía trigger DB + service layer
**Opción**: trigger `BEFORE UPDATE/DELETE` en la tabla `audit_log` que rechaza la operación + `AuditService` que nunca expone métodos de update/delete.

**Por qué**: doble seguridad. Si un error de código intenta modificar/borrar, el trigger lo frena en DB. Si alguien conecta directo a la DB, el trigger aplica igual. El service layer ni siquiera tiene métodos que lo intenten.

### D2 — RequestContext vía `request.state`
**Opción**: middleware que extrae `X-Forwarded-For` (o `remote_addr`) y `User-Agent` del request y los guarda en `request.state.ip` y `request.state.user_agent`. El `AuditService` los obtiene de ahí.

**Por qué**: evita pasar IP y user_agent como parámetros en cada llamada al AuditService. El middleware se ejecuta una vez por request y deja el contexto disponible. Alternativa considerada: inyectar como dependencia FastAPI (`request: Request = Depends(get_request_context)`), pero eso obliga a cada endpoint a declarar la dependencia. `request.state` es el approach estándar en FastAPI/Starlette para datos transversales.

### D3 — Impersonación vía JWT claim `es_impersonacion: true`
**Opción**: al iniciar impersonación, el backend emite un nuevo JWT access con `es_impersonacion: true` y `impersonado_id` como claims adicionales. `get_current_user` detecta `es_impersonacion` y carga el usuario impersonado para permisos, pero el AuditService siempre usa el `actor_id` original.

**Por qué**: el JWT es firmado — no se puede falsear. Cada request sabe si está bajo impersonación. No requiere estado en servidor (sesión, cache). Alternativa: tabla de sesiones activas de impersonación, pero agrega latencia y estado que el JWT ya resuelve.

### D4 — Códigos de acción como catálogo fijo (enum Python)
**Opción**: clase `AuditAction` con constantes tipadas (`CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"`) validadas por Pydantic.

**Por qué**: RN-24 exige catálogo cerrado. Un enum previene typos y permite que el IDE autocomplete. Alternativa: tabla en DB — más flexible pero prematuro; si el catálogo crece mucho, se migra a DB después.

## Risks / Trade-offs

- **[Risk] Trigger DB no portable**: el trigger `BEFORE UPDATE/DELETE` usa PL/pgSQL, que es PostgreSQL-specific. **Mitigación**: es una decisión deliberada (PostgreSQL es el motor único). Si se cambia de motor, el trigger se reimplementa.
- **[Risk] JWT impersonación revocación**: un JWT de impersonación, una vez emitido, es válido hasta su expiración (15 min). **Mitigación**: duración corta (configurable como ACCESS_TOKEN_EXPIRE_MINUTES). Para revocación inmediata se necesitaría una lista negra (fuera de scope por ahora).
- **[Trade-off] AuditMiddleware captura IP de X-Forwarded-For**: si no hay proxy, usa `request.client.host`. El dato puede no ser 100% confiable si el cliente miente en headers, pero es el estándar de la industria.
- **[Trade-off] Seed de códigos en migración 0004**: los códigos nuevos que agreguen changes futuros requerirán nuevas migraciones para insertarlos en el catálogo. Alternativa más ágil: migrar a tabla en DB cuando el catálogo supere ~20 entradas.
