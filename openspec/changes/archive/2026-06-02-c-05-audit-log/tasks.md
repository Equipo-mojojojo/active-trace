## 1. Modelo AuditLog + Migración

- [x] 1.1 Crear `backend/app/models/audit_log.py` con modelo AuditLog (id, tenant_id, fecha_hora, actor_id, impersonado_id, materia_id, accion, detalle JSONB, filas_afectadas, ip, user_agent)
- [x] 1.2 Registrar AuditLog en `backend/app/models/__init__.py`
- [x] 1.3 Generar migración Alembic `0004_create_audit_log.py` con tabla `audit_log` + trigger DB `no_audit_update_delete` (rechaza UPDATE/DELETE)
- [x] 1.4 Seed de códigos de acción en migración 0004 (insertar en tabla de catálogo o documentar como constantes)
- [x] 1.5 Escribir test de modelo: creación de registro, campos obligatorios

## 2. Append-only Enforcement

- [x] 2.1 Escribir test: UPDATE sobre audit_log es rechazado por trigger DB
- [x] 2.2 Escribir test: DELETE sobre audit_log es rechazado por trigger DB
- [x] 2.3 Verificar que AuditService no expone métodos de update/delete

## 3. AuditService

- [x] 3.1 Crear `backend/app/core/audit_constants.py` con clase `AuditAction` (catálogo de códigos como constantes tipadas)
- [x] 3.2 Crear `backend/app/services/audit_service.py` con `AuditService.register(actor_id, tenant_id, accion, *, impersonado_id, materia_id, detalle, filas_afectadas)`
- [x] 3.3 AuditService obtiene ip y user_agent desde `request.state` (RequestContext del middleware)
- [x] 3.4 AuditService valida accion contra catálogo AuditAction — lanza ValueError si inválido
- [x] 3.5 AuditService usa `actor_id` = usuario real y `impersonado_id` = usuario impersonado cuando hay impersonación activa
- [x] 3.6 Escribir test de AuditService: registro exitoso con todos los campos
- [x] 3.7 Escribir test: código inválido lanza ValueError
- [x] 3.8 Escribir test: registro bajo impersonación atribuye al actor real

## 4. AuditMiddleware

- [x] 4.1 Crear `backend/app/core/audit_middleware.py` con middleware que captura IP (X-Forwarded-For / remote_addr) y User-Agent, los guarda en `request.state`
- [x] 4.2 Registrar middleware en `backend/app/main.py`
- [x] 4.3 Escribir test: middleware captura IP de X-Forwarded-For
- [x] 4.4 Escribir test: middleware captura remote_addr cuando no hay proxy
- [x] 4.5 Escribir test: User-Agent capturado correctamente

## 5. API de Consulta del Log de Auditoría

- [x] 5.1 Crear `backend/app/schemas/audit.py` con AuditLogResponse (Pydantic, extra='forbid')
- [x] 5.2 Crear `backend/app/api/v1/routers/audit.py` con GET /api/admin/audit-log
- [x] 5.3 Implementar filtros: desde/hasta (fechas), actor_id, materia_id, accion, page, page_size
- [x] 5.4 Proteger endpoint con `require_permission("auditoria:ver")`
- [x] 5.5 Soporte para `auditoria:ver:propio`: filtrar solo registros del usuario actual
- [x] 5.6 Registrar router en `backend/app/main.py`
- [x] 5.7 Escribir test de integración: listar log sin filtros
- [x] 5.8 Escribir test: filtrar por fechas, actor, acción, materia
- [x] 5.9 Escribir test: 403 sin permiso auditoria:ver
- [x] 5.10 Escribir test: scoping :propio solo muestra acciones del usuario

## 6. Impersonación

- [x] 6.1 Crear `backend/app/api/v1/routers/impersonacion.py` con POST /api/admin/impersonacion/iniciar y POST /api/admin/impersonacion/finalizar
- [x] 6.2 Proteger con `require_permission("impersonacion:usar")`
- [x] 6.3 Iniciar: validar que usuario_id exista, emitir JWT access con `es_impersonacion: true` e `impersonado_id`, registrar `IMPERSONACION_INICIAR` en audit_log
- [x] 6.4 Finalizar: emitir nuevo JWT access normal, registrar `IMPERSONACION_FINALIZAR` en audit_log
- [x] 6.5 Modificar `get_current_user` en `backend/app/core/dependencies.py`: si `es_impersonacion: true` en JWT, cargar usuario impersonado y guardar actor_real en `request.state.actor_real`
- [x] 6.6 Registrar router en `backend/app/main.py`
- [x] 6.7 Escribir test: iniciar impersonación exitosamente
- [x] 6.8 Escribir test: 403 sin permiso impersonacion:usar
- [x] 6.9 Escribir test: 404 usuario inexistente
- [x] 6.10 Escribir test: finalizar impersonación
- [x] 6.11 Escribir test: get_current_user bajo impersonación devuelve usuario impersonado
- [x] 6.12 Escribir test: audit log bajo impersonación atribuye al actor real

## 7. Limpieza y Verificación Final

- [x] 7.1 Verificar que todos los archivos nuevos tengan ≤500 LOC
- [x] 7.2 Verificar que ningún schema Pydantic tenga `extra='forbid'` faltante
- [x] 7.3 Ejecutar suite completa de tests y confirmar que todo pasa
- [x] 7.4 Marcar C-05 como completado en CHANGES.md
