## Why

El sistema necesita un modelo de autorización granular y administrable. Hoy existe autenticación (C-03) con JWT que transporta roles como strings, pero no hay un mecanismo que resuelva permisos finos (`modulo:accion`) a partir de esos roles, ni que permita administrar la matriz rol × permiso como datos. Sin esto, no se puede construir ninguna feature protegida (C-05 en adelante) ni garantizar el principio fail-closed. C-04 es el gate que habilita el primer fork de paralelismo (GATE 4).

## What Changes

- Nuevos modelos SQLAlchemy: `Rol`, `Permiso`, `RolPermiso` con datos seed de la matriz documentada.
- Migración Alembic 002 que crea las tablas y siembra los 7 roles del dominio con sus ~35 permisos.
- Dependency `require_permission("modulo:accion")` como FastAPI guard que deniega 403 si el usuario no tiene el permiso.
- Resolución de permisos efectivos server-side: unión de permisos de todos los roles del usuario, acotada por tenant.
- Cache en memoria de permisos efectivos por (tenant_id, user_id) con invalidación al modificar asignaciones.
- Mecanismo de scoping `:propio` para permisos que solo aplican sobre recursos propios (validación en service layer).
- Endpoints para administrar el catálogo de roles y permisos (CRUD protegido con `rbac:gestionar`).
- Refactor menor en `get_current_user` para exponer permisos resueltos si es necesario.

## Capabilities

### New Capabilities
- `rbac-core-models`: Modelos Rol, Permiso, RolPermiso con herencia TenantScoped, migración 002, seed data de la matriz de capacidades (7 roles, ~35 permisos).
- `rbac-permission-guard`: FastAPI dependency `require_permission` que verifica permisos server-side, con soporte de caché y scoping `:propio` para recursos propios.
- `rbac-admin-api`: Endpoints CRUD para administrar roles y permisos del tenant, protegidos con permiso `rbac:gestionar`.

### Modified Capabilities
- *(ninguna — C-04 no cambia requirements de specs existentes)*

## Impact

- **Código nuevo**: `backend/app/models/role.py`, `backend/app/models/permission.py`, `backend/app/core/permissions.py`, `backend/app/repositories/role_repository.py`, `backend/app/services/role_service.py`, `backend/app/schemas/role.py`, `backend/app/api/v1/routers/roles.py`
- **Modificaciones menores**: `backend/app/core/dependencies.py` (agregar `require_permission`), `backend/app/models/__init__.py` (registrar nuevos modelos)
- **Migración**: nueva migración Alembic 002
- **Tests**: nuevos archivos de test para cada capa
- **Dependencias**: ninguna externa nueva (solo SQLAlchemy + FastAPI ya instalados)
