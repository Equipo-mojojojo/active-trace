## 1. Modelos RBAC + Migración

- [x] 1.1 Crear `backend/app/models/role.py` con modelo Rol (id, tenant_id, nombre, descripcion, editable, timestamps, soft delete)
- [x] 1.2 Crear `backend/app/models/permission.py` con modelo Permiso (id, tenant_id, codigo, modulo, accion, descripcion, timestamps)
- [x] 1.3 Crear `backend/app/models/role_permission.py` con modelo RolPermiso (rol_id, permiso_id, tenant_id, PK compuesta)
- [x] 1.4 Registrar los 3 modelos en `backend/app/models/__init__.py`
- [x] 1.5 Escribir test de modelos: creación, unicidad por tenant, soft delete, herencia TenantScopedModelMixin
- [x] 1.6 Escribir test de aislamiento multi-tenant: un tenant no ve roles de otro
- [x] 1.7 Generar migración Alembic 003 con las 3 tablas

## 2. Seed Data de la Matriz de Capacidades

- [x] 2.1 Escribir script de seed con los 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS)
- [x] 2.2 Definir catálogo de ~35 permisos según matriz de `knowledge-base/03_actores_y_roles.md §3.3`
- [x] 2.3 Implementar seed de asignaciones rol-permiso en migración 003
- [x] 2.4 Escribir test de seed: verificar que cada rol tenga los permisos correctos

## 3. Resolución de Permisos Efectivos

- [x] 3.1 Implementar `get_effective_permissions(user_id, tenant_id)` en `backend/app/core/permissions.py`
- [x] 3.2 Implementar caché LRU de permisos con clave `{tenant_id}:{user_id}` en `backend/app/core/permissions.py`
- [x] 3.3 Escribir test de resolución de permisos: unión de roles, permisos correctos por rol
- [x] 3.4 Escribir test de caché: hit, miss, invalidación al modificar asignaciones
- [x] 3.5 Crear `backend/app/repositories/role_repository.py` con queries de resolución de permisos (scope tenant siempre activo)

## 4. Guard `require_permission` como FastAPI Dependency

- [x] 4.1 Implementar `require_permission(codigo: str)` como clase guard en `backend/app/core/permissions.py`
- [x] 4.2 Integrar con `get_current_user` existente para resolver el usuario autenticado
- [x] 4.3 Escribir test: usuario con permiso → 200, usuario sin permiso → 403, usuario no autenticado → 401
- [x] 4.4 Escribir test: fail-closed — error de DB → 403

## 5. Scoping `:propio` para Permisos sobre Recursos Propios

- [x] 5.1 Implementar helper `has_permission_with_scope(permiso_base, user, resource_owner_id, db)` en permissions.py
- [x] 5.2 El helper retorna True si el usuario tiene el permiso global o el permiso `:propio` + es dueño del recurso
- [x] 5.3 Escribir test: permiso global pasa sin verificar dueño, permiso `:propio` verifica dueño, sin permiso → False

## 6. API de Administración de Roles y Permisos

- [x] 6.1 Crear `backend/app/schemas/role.py` con Pydantic schemas (RoleCreate, RoleUpdate, RoleResponse, PermissionAssign), todos con `extra='forbid'`
- [x] 6.2 Crear `backend/app/services/role_service.py` con lógica de CRUD de roles y asignación de permisos
- [x] 6.3 Crear `backend/app/api/v1/routers/roles.py` con endpoints protegidos con `require_permission("rbac:gestionar")`
- [x] 6.4 GET /api/v1/admin/roles — listar roles del tenant
- [x] 6.5 POST /api/v1/admin/roles — crear rol (con validación de unicidad)
- [x] 6.6 PUT /api/v1/admin/roles/{id} — actualizar rol
- [x] 6.7 DELETE /api/v1/admin/roles/{id} — soft delete
- [x] 6.8 GET /api/v1/admin/permisos — listar catálogo (con filtro opcional por módulo)
- [x] 6.9 POST /api/v1/admin/roles/{id}/permisos — asignar permiso a rol
- [x] 6.10 DELETE /api/v1/admin/roles/{id}/permisos/{permiso_id} — remover permiso (invalida caché)
- [x] 6.11 Escribir tests de integración para cada endpoint: 200 OK, 403 sin permiso, 409 conflicto, 404 rol no encontrado
- [x] 6.12 Escribir test de invalidación de caché al modificar asignaciones de permisos

## 7. Limpieza y Verificación Final

- [x] 7.1 Verificar que todos los archivos nuevos tengan ≤500 LOC
- [x] 7.2 Verificar que ningún schema Pydantic tenga `extra='forbid'` faltante
- [x] 7.3 Verificar cobertura ≥80% líneas en los módulos nuevos
- [x] 7.4 Ejecutar suite completa de tests y confirmar que todo pasa — 26/27 OK, 1 preexistente
- [x] 7.5 Marcar C-04 como completado en CHANGES.md
