## ADDED Requirements

### Requirement: El sistema SHALL proveer un guard `require_permission` como FastAPI dependency
El sistema SHALL implementar `require_permission(codigo: str)` como una FastAPI dependency que:
- Resuelve el usuario autenticado via `get_current_user`
- Obtiene los permisos efectivos del usuario
- Si el permiso NO está en el conjunto efectivo → HTTP 403 Forbidden
- Si el permiso SÍ está → permite continuar la ejecución

#### Scenario: Usuario con permiso accede al endpoint
- **WHEN** un usuario con permiso `calificaciones:importar` llama a un endpoint protegido con `require_permission("calificaciones:importar")`
- **THEN** el sistema permite el acceso

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario SIN permiso `calificaciones:importar` llama al endpoint protegido
- **THEN** el sistema retorna HTTP 403 Forbidden

#### Scenario: Usuario no autenticado recibe 401
- **WHEN** un usuario no autenticado llama a un endpoint protegido
- **THEN** el sistema retorna HTTP 401 Unauthorized (antes de llegar al guard)

### Requirement: El sistema SHALL cachear permisos efectivos en memoria
El sistema SHALL mantener un caché LRU en memoria de los permisos efectivos por clave `{tenant_id}:{user_id}` → `set[str]` de códigos.

#### Scenario: Cache hit retorna permisos sin query a DB
- **WHEN** se resuelven permisos para un usuario ya cacheados
- **THEN** el sistema NO ejecuta queries a las tablas rol/permiso

#### Scenario: Invalidez de caché al modificar asignaciones
- **WHEN** se modifica la asignación de permisos de un rol (via admin API)
- **THEN** el sistema invalida las entradas de caché de todos los usuarios que tienen ese rol

### Requirement: El sistema SHALL soportar scoping `:propio` en permisos
Los permisos con sufijo `:propio` (ej: `calificaciones:importar:propio`) SHALL ser verificados en dos niveles:
1. El guard `require_permission` verifica que el usuario tenga el permiso con o sin `:propio`
2. El service layer valida que el recurso pertenezca al usuario (contexto: materia, comisión)

#### Scenario: Permiso propio válido
- **WHEN** un PROFESOR intenta importar calificaciones de su propia comisión
- **THEN** el guard permite el acceso y el service valida la pertenencia

#### Scenario: Permiso propio sobre recurso ajeno
- **WHEN** un PROFESOR intenta importar calificaciones de una comisión que NO es suya
- **THEN** el guard permite el acceso (tiene el permiso base), pero el service retorna HTTP 403

#### Scenario: Permiso global sin restricción
- **WHEN** un ADMIN (con `calificaciones:importar` sin `:propio`) importa calificaciones de cualquier comisión
- **THEN** el guard permite el acceso y el service NO valida pertenencia

### Requirement: El guard SHALL ser fail-closed
Ante cualquier error en la resolución de permisos (DB error, excepción inesperada), el sistema SHALL denegar el acceso con HTTP 403.

#### Scenario: Error de base de datos al resolver permisos
- **WHEN** la base de datos no responde al resolver permisos
- **THEN** el sistema retorna HTTP 403 (no permite el acceso por defecto)
