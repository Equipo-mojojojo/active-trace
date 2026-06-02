## ADDED Requirements

### Requirement: El sistema SHALL exponer endpoints CRUD para roles
El sistema SHALL proveer una API REST bajo `/api/v1/admin/roles` para administrar roles del tenant:

- `GET /api/v1/admin/roles` — listar roles (incluye conteo de usuarios asignados)
- `POST /api/v1/admin/roles` — crear nuevo rol
- `PUT /api/v1/admin/roles/{id}` — actualizar nombre y descripción
- `DELETE /api/v1/admin/roles/{id}` — eliminar rol (soft delete, falla si tiene usuarios activos)

#### Scenario: Listar roles del tenant
- **WHEN** un usuario con permiso `rbac:gestionar` hace GET a `/api/v1/admin/roles`
- **THEN** el sistema retorna la lista de roles del tenant, excluyendo soft-deleted

#### Scenario: Crear rol válido
- **WHEN** se envía POST a `/api/v1/admin/roles` con `{"nombre": "AUXILIAR", "descripcion": "Asistente de cátedra"}`
- **THEN** el sistema crea y retorna el nuevo rol con HTTP 201

#### Scenario: Crear rol con nombre duplicado
- **WHEN** se envía POST con un nombre de rol que ya existe en el tenant
- **THEN** el sistema retorna HTTP 409 Conflict

#### Scenario: Soft delete de rol sin usuarios activos
- **WHEN** se envía DELETE a `/api/v1/admin/roles/{id}` y el rol no tiene usuarios activos
- **THEN** el sistema marca deleted_at y retorna HTTP 204

### Requirement: El sistema SHALL exponer endpoints para gestionar el catálogo de permisos
El sistema SHALL proveer:
- `GET /api/v1/admin/permisos` — listar catálogo de permisos del tenant (con filtro opcional por módulo)

#### Scenario: Listar permisos
- **WHEN** un administrador hace GET a `/api/v1/admin/permisos`
- **THEN** el sistema retorna todos los permisos del catálogo

#### Scenario: Filtrar permisos por módulo
- **WHEN** se hace GET a `/api/v1/admin/permisos?modulo=calificaciones`
- **THEN** el sistema retorna solo los permisos del módulo `calificaciones`

### Requirement: El sistema SHALL exponer endpoints para asignar/remover permisos a roles
- `POST /api/v1/admin/roles/{id}/permisos` — asignar permiso `{"permiso_id": "uuid"}`
- `DELETE /api/v1/admin/roles/{id}/permisos/{permiso_id}` — remover permiso del rol

#### Scenario: Asignar permiso a rol
- **WHEN** se envía POST a `/api/v1/admin/roles/{id}/permisos` con un permiso_id válido
- **THEN** el sistema asigna el permiso al rol y retorna HTTP 201

#### Scenario: Remover permiso de rol
- **WHEN** se envía DELETE a `/api/v1/admin/roles/{id}/permisos/{permiso_id}`
- **THEN** el sistema remueve la asignación e invalida el caché de permisos

### Requirement: Todos los endpoints de administración SHALL estar protegidos con `require_permission("rbac:gestionar")`
Sin este permiso, cualquier endpoint bajo `/api/v1/admin/roles` y `/api/v1/admin/permisos` retorna HTTP 403.

#### Scenario: Acceso sin permiso
- **WHEN** un usuario sin permiso `rbac:gestionar` intenta acceder a cualquier endpoint de admin
- **THEN** el sistema retorna HTTP 403 Forbidden
