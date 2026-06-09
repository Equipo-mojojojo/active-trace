## ADDED Requirements

### Requirement: Estructura académica con tab-per-entidad
El sistema SHALL mostrar en `EstructuraAcademicaPage` (ruta `/admin/estructura`) tres tabs: "Carreras", "Cohortes" y "Materias". Cada tab SHALL renderizar su propia tabla con botón "Nueva" e inline edit/delete, consultando su endpoint correspondiente.

#### Scenario: Render de los tres tabs
- **WHEN** un usuario con `estructura:gestionar` navega a `/admin/estructura`
- **THEN** ve los tabs "Carreras", "Cohortes" y "Materias" con "Carreras" activo por defecto

### Requirement: ABM de carreras
El sistema SHALL listar carreras (`GET /api/admin/carreras`) con columnas código, nombre, estado (badge: Activa verde / Inactiva gris) y acciones inline. SHALL permitir crear (`POST`), editar (`PUT /api/admin/carreras/{id}`) y soft-delete (`DELETE /api/admin/carreras/{id}`).

#### Scenario: Crear carrera
- **WHEN** el usuario hace click en "Nueva carrera", completa código y nombre, y guarda
- **THEN** se hace POST y la carrera aparece en la tabla con estado "Activa"

#### Scenario: Código duplicado
- **WHEN** el backend responde 409 por código duplicado
- **THEN** la fila en edición muestra el error inline sin descartar los datos

#### Scenario: Cambiar estado a Inactiva
- **WHEN** el usuario edita una carrera y cambia su estado a "Inactiva", y guarda
- **THEN** se hace PUT y la fila muestra el badge "Inactiva" en gris

#### Scenario: Eliminar (soft delete) carrera
- **WHEN** el usuario elimina una carrera y confirma
- **THEN** se hace DELETE y la carrera deja de aparecer en la tabla

### Requirement: ABM de cohortes
El sistema SHALL listar cohortes (`GET /api/admin/cohortes`) con columnas carrera, nombre, año, vigencia desde/hasta y estado. SHALL permitir crear, editar y eliminar (`/api/admin/cohortes`). El formulario de cohorte SHALL incluir selección de `carrera_id`.

#### Scenario: Crear cohorte
- **WHEN** el usuario crea una cohorte con carrera, nombre, año y vigencia desde, y guarda
- **THEN** se hace POST y la cohorte aparece en la tabla

#### Scenario: Nombre duplicado en la misma carrera
- **WHEN** el backend responde 409 por nombre duplicado para `(carrera_id, nombre)`
- **THEN** la fila muestra el error inline

### Requirement: ABM de materias
El sistema SHALL listar materias (`GET /api/admin/materias`) con columnas código, nombre y estado. SHALL permitir crear, editar (incluyendo `grupo_plus_clave`) y eliminar (`/api/admin/materias`).

#### Scenario: Crear materia
- **WHEN** el usuario crea una materia con código y nombre, y guarda
- **THEN** se hace POST y la materia aparece en la tabla

#### Scenario: Asignar grupo_plus_clave
- **WHEN** el usuario edita una materia y setea `grupo_plus_clave` a "PROG", y guarda
- **THEN** se hace PUT y la materia conserva esa clave

### Requirement: Protección de acceso a estructura académica
La ruta `/admin/estructura` SHALL estar protegida por `AuthGuard` + `PermissionGuard` con permiso `estructura:gestionar`.

#### Scenario: Acceso sin permiso
- **WHEN** un usuario sin `estructura:gestionar` navega a `/admin/estructura`
- **THEN** la app redirige a `/403`
