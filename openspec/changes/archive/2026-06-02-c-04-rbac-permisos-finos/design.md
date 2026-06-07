## Context

El proyecto activia-trace implementa autenticación vía JWT (C-03) con roles transportados como lista de strings en el token y almacenados como JSON en `User.roles`. Sin embargo, no existe un mecanismo de autorización que resuelva qué acciones concretas (`modulo:accion`) puede ejecutar un usuario a partir de sus roles. Toda la lógica de negocio futura (C-05 en adelante) depende de este cimiento.

El modelo de dominio está documentado en `knowledge-base/03_actores_y_roles.md`: 7 roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) con una matriz de ~35 permisos finos. La arquitectura objetivo se describe en `docs/ARQUITECTURA.md §5.2`.

**Estado actual relevante:**
- `backend/app/core/permissions.py` — placeholder vacío
- `backend/app/core/dependencies.py` — `get_current_user` existente que resuelve user + roles desde JWT
- `backend/app/models/user.py` — `roles: Mapped[list[str]]` como columna JSON
- Migración 001: tenant (C-02) ya aplicada

**Restricciones:**
- Governance CRITICO: requiere aprobación explícita antes de escribir código de implementación
- Máximo 500 LOC por archivo backend
- Snake_case en Python, Pydantic schemas con `extra='forbid'`
- TDD estricto: test que falla → código mínimo → triangulación → refactor
- Cobertura ≥80% líneas, ≥90% reglas de negocio

## Goals / Non-Goals

**Goals:**
- Modelar RBAC con catálogo administrable de roles, permisos y su relación (tablas, no hardcode)
- Proveer un guard `require_permission("modulo:accion")` como FastAPI dependency que retorne 403 si el usuario no tiene el permiso
- Resolver permisos efectivos server-side como unión de permisos de todos los roles del usuario, scoped por tenant
- Sembrar la matriz de capacidades documentada (7 roles, ~35 permisos) via migración Alembic
- Soportar scoping `:propio` para permisos que solo aplican sobre recursos del usuario (validación en service layer, no en router)
- Cachear en memoria la resolución de permisos por (tenant_id, user_id) para evitar N+1 queries
- Exponer API de administración del catálogo protegida con permiso `rbac:gestionar`
- Mantener compatibilidad con User.roles como denormalización para JWT (sin migración forzosa de User)

**Non-Goals:**
- No se modifica el modelo User ni sus columnas existentes (User.roles se mantiene como cache)
- No se implementa la lógica de negocio de asignación de roles a usuarios (eso es C-07)
- No se implementa vigencia temporal de asignaciones (alcance parcial, se completa en C-07)
- No se toca el frontend (es C-21 en adelante)

## Decisions

### D1 — Modelos como tablas separadas (Rol, Permiso, RolPermiso) vs. JSON en User

| Opción | Pros | Contras |
|--------|------|---------|
| **Tablas separadas** ✅ | Integridad referencial, administrable, consultable, extensible | Migración adicional, más queries |
| JSON en User | Simple, sin migración | No consultable, frágil, no extensible |

**Decisión**: Tablas separadas. El JSON `User.roles` se mantiene como denormalización para el claim `roles` del JWT, pero la fuente de verdad de los permisos por rol es la tabla `RolPermiso`. Esto permite que en C-07 la asignación de roles a usuarios sea robusta.

### D2 — Formato de permisos y scoping `:propio`

El permiso `(propio)` en la matriz (ej: PROFESOR tiene `calificaciones:importar(propio)`) implica que el usuario solo puede operar sobre sus propios recursos. Se implementa como sufijo en el código del permiso:

```
calificaciones:importar         → permiso global (ADMIN, COORDINADOR)
calificaciones:importar:propio  → permiso scoped (PROFESOR)
```

El guard `require_permission` verifica el permiso base. El scoping `:propio` se valida en el **service layer**, no en el router, comparando el contexto del recurso (comisión, materia) contra las asignaciones del usuario. Esto evita acoplar la capa HTTP a la lógica de scoping.

### D3 — Caché de permisos en memoria

Se implementa un caché LRU simple en `core/permissions.py` con clave `{tenant_id}:{user_id}` → `set[str]` de códigos de permiso.

| Aspecto | Detalle |
|---------|---------|
| Estructura | `dict` con clave compuesta string, valor `set[str]` |
| TTL | Sin expiración por tiempo; invalidación explícita |
| Invalidación | Cuando se modifican roles o RolPermiso (desde el service de administración) |
| Tamaño máximo | LRU de 1000 entradas (configurable) |
| Atomicidad | No requiere locks porque FastAPI es single-thread por request |

**Alternativa considerada**: Redis. Se descarta porque la carga de resolución de permisos no justifica la sobrecarga operativa. Si en el futuro escala, se reemplaza el backend de caché sin cambiar la interfaz.

### D4 — Resolución de permisos server-side (no en JWT)

Los permisos NO se almacenan en el JWT. Solo viajan los roles. Cada request resuelve los permisos efectivos desde la base de datos (con caché). Esto evita tokens grandes y el problema de permisos stale durante la vida del access token.

**Alternativa considerada**: Embedir permisos en JWT. Se descarta porque (a) los tokens crecerían ~1KB, (b) al rotar permisos habría ventana de inconsistencia hasta que expire el access token (15 min), (c) viola el principio de "los permisos se resuelven server-side" de la arquitectura.

### D5 — Endpoints de administración bajo router `/api/v1/admin/roles`

```python
GET    /api/v1/admin/roles         → listar roles del tenant
POST   /api/v1/admin/roles         → crear rol
PUT    /api/v1/admin/roles/{id}    → actualizar rol
DELETE /api/v1/admin/roles/{id}    → eliminar rol (soft delete)
GET    /api/v1/admin/permisos      → listar catálogo de permisos
POST   /api/v1/admin/roles/{id}/permisos → asignar permiso a rol
DELETE /api/v1/admin/roles/{id}/permisos/{permiso_id} → quitar permiso
```

Todos protegidos con `require_permission("rbac:gestionar")`.

## Entity Relationship

```
┌─────────────────────────┐
│  Rol                    │
│─────────────────────────│
│  id: UUID (PK)          │
│  tenant_id: UUID (FK)   │
│  nombre: str (único x   │
│           tenant)       │
│  descripcion: str       │
│  editable: bool         │
│  created_at             │
│  updated_at             │
│  deleted_at (soft)      │
└────────────┬────────────┘
             │ 1:N
             │
┌────────────▼────────────┐
│  RolPermiso              │
│─────────────────────────│
│  rol_id: UUID (FK)      │
│  permiso_id: UUID (FK)  │
│  tenant_id: UUID (FK)   │
│  PK: (rol_id,           │
│       permiso_id,       │
│       tenant_id)        │
└────────────┬────────────┘
             │ N:1
             │
┌────────────▼────────────┐
│  Permiso                │
│─────────────────────────│
│  id: UUID (PK)          │
│  tenant_id: UUID (FK)   │
│  codigo: str (único)    │
│  modulo: str            │
│  accion: str            │
│  descripcion: str       │
└─────────────────────────┘
```

**Nota**: `Permiso.codigo` = `"{modulo}:{accion}"` (ej: `calificaciones:importar`). La tabla `Permiso` es catálogo global por tenant; `RolPermiso` asigna qué roles tienen cada permiso.

## Migration Plan

### Migración 002: `rbac_core`

```python
"""Create role, permission, role_permission tables + seed data.

Revision ID: 002
Revises: 001
"""
```

**Seed data** (7 roles + ~35 permisos de la matriz en `03_actores_y_roles.md §3.3`):

- Crear roles: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
- Crear permisos: `propio:ver_estado`, `evaluacion:reservar`, `aviso:ack`, `calificaciones:importar`, `calificaciones:importar:propio`, `atrasados:ver`, `atrasados:ver:propio`, `entregas:ver_sin_corregir`, `entregas:ver_sin_corregir:propio`, `comunicacion:enviar`, `comunicacion:enviar:propio`, `comunicacion:aprobar`, `encuentros:gestionar`, `encuentros:gestionar:propio`, `guardias:registrar`, `guardias:registrar:propio`, `tareas:gestionar`, `tareas:gestionar:propio`, `avisos:publicar`, `equipos:asignar`, `estructura:gestionar`, `usuarios:gestionar`, `auditoria:ver`, `auditoria:ver:propio`, `liquidaciones:operar`, `liquidaciones:cerrar`, `facturas:gestionar`, `tenant:configurar`, `rbac:gestionar`, `impersonacion:usar`
- Asignar permisos según matriz de capacidades

**Rollback**: `op downgrade()` elimina las tablas.

### Archivos nuevos
```
backend/app/models/role.py
backend/app/models/permission.py
backend/app/models/__init__.py (modificado)
backend/app/core/permissions.py (implementación)
backend/app/core/dependencies.py (modificado)
backend/app/repositories/role_repository.py
backend/app/services/role_service.py
backend/app/schemas/role.py
backend/app/api/v1/routers/roles.py
backend/alembic/versions/002_rbac_core.py
```

## Risks / Trade-offs

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Caché de permisos sirve datos stale si no se invalida correctamente | Usuario mantiene acceso a un permiso que le fue revocado | Invalidación explícita en el admin service + LRU bound. En futura iteración agregar TTL |
| `User.roles` (JSON) se desincroniza de los roles reales en tabla Rol | Inconsistencia: JWT muestra roles que ya no tiene | C-07 syncronizará la asignación. Por ahora es riesgo aceptado (cosmético) |
| N+1 queries si el caché está frío y hay múltiples guards en un mismo request | ~3 queries por request | El caché LRU mitiga. Además se puede cargar permisos en `get_current_user` si se detecta patrón |
| Rol NEXO tiene semántica no completamente definida (PA-25) | Seed incorrecto | Se seedea con permisos mínimos documentados. Se revisa cuando se cierre PA-25 |
| La tabla `Permiso` es catálogo por tenant → duplicación de ~35 permisos x N tenants | Aumento de filas | Aceptable: 35 filas x 100 tenants = 3500 filas. Indexado por código |

## Open Questions

- **NEXO**: La semántica exacta del rol está en discusión (PA-25). Se seedea con permisos de visibilidad + comunicación. Revisar cuando se cierre la pregunta.
- **`rbac:gestionar`**: ¿Quién tiene este permiso? Solo ADMIN por ahora. ¿COORDINADOR debería poder gestionar sub-roles? Se define en C-07.
