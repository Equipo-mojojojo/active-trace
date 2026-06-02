## Why

El sistema **no tiene registro de auditoría**. Toda acción significativa (importaciones, envíos, cambios de estado, impersonación) debe quedar registrada con actor, timestamp, contexto y resultado. Sin auditoría no hay trazabilidad — y el nombre del producto es *trace*.

Este cambio implementa el modelo `AuditLog` append-only, el servicio de registro, el middleware de captura de contexto de request (IP, user agent), el mecanismo de impersonación (inicio/fin con sesión distinguible), y la API de consulta del log.

## What Changes

- Nuevo modelo `AuditLog` (E-AUD) con campos: actor_id, impersonado_id (nullable), materia_id (nullable), accion, detalle (JSON), filas_afectadas, ip, user_agent, fecha_hora
- **Append-only enforcement**: trigger en DB que rechaza UPDATE/DELETE sobre `audit_log`; sin endpoints de modificación ni borrado a nivel app
- AuditService: helper para registrar acciones con código estandarizado (`CALIFICACIONES_IMPORTAR`, `COMUNICACION_ENVIAR`, etc.)
- **AuditMiddleware**: captura IP y user_agent por request, los inyecta para que AuditService los use sin repetirlos en cada llamada
- **Impersonación**: endpoints `POST /api/admin/impersonacion/iniciar` y `POST /api/admin/impersonacion/finalizar` + sesión distinguible (`es_impersonacion: true` en claims JWT). Atribución siempre al actor real
- API de consulta: `GET /api/admin/audit-log` con filtros por rango de fechas, actor, materia, código de acción
- `Migración 0004: audit_log` + seed de códigos de acción
- Protección con `require_permission("auditoria:ver")` para consulta; `require_permission("impersonacion:usar")` para impersonación

## Capabilities

### New Capabilities
- `audit-log-model`: Modelo AuditLog append-only, trigger DB anti-update/delete, migración 0004
- `audit-service`: Servicio de registro de acciones con códigos estandarizados, integración con middleware de request context
- `audit-middleware`: Middleware FastAPI que captura IP y user_agent por request, los provee al AuditService
- `audit-admin-api`: API REST de consulta del log de auditoría con filtros
- `impersonation`: Endpoints de inicio/fin de impersonación, sesión distinguible, auditoría obligatoria

### Modified Capabilities
- *(ninguna — es el primer módulo de auditoría)*

## Impact

- **Nuevo archivo**: `backend/app/models/audit_log.py`
- **Nuevo archivo**: `backend/app/services/audit_service.py`
- **Nuevo archivo**: `backend/app/core/audit_middleware.py`
- **Nuevo archivo**: `backend/app/api/v1/routers/audit.py`
- **Nuevo archivo**: `backend/app/api/v1/routers/impersonacion.py`
- **Nuevo archivo**: `backend/app/schemas/audit.py`
- **Nuevo archivo**: `backend/alembic/versions/0004_create_audit_log.py`
- **Modificado**: `backend/app/models/__init__.py` — registrar AuditLog
- **Modificado**: `backend/app/main.py` — registrar routers y middleware
- **Dependencias**: C-04 (RBAC) ya provee `auditoria:ver` e `impersonacion:usar` en seed
- **Base de datos**: nueva tabla `audit_log`, trigger `no_audit_update_delete`
