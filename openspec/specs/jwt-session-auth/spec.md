## ADDED Requirements

### Requirement: Login con email y password hasheado

El sistema SHALL autenticar usuarios mediante email y password verificados contra credenciales persistidas con hashing Argon2id. Solo usuarios válidos y activos del tenant correspondiente SHALL poder iniciar sesión.

#### Scenario: Credenciales válidas emiten autenticación
- **WHEN** un usuario activo provee email y password correctos
- **THEN** el sistema acepta la autenticación primaria

#### Scenario: Credenciales inválidas son rechazadas
- **WHEN** el email no existe o el password no coincide
- **THEN** el sistema rechaza el intento sin emitir sesión válida

### Requirement: Sesión con access token corto y refresh rotation

El sistema SHALL emitir una sesión compuesta por un access token JWT de vida corta y un refresh token con rotación. Cada uso exitoso del refresh token SHALL invalidar el refresh anterior y emitir un nuevo par de tokens.

#### Scenario: Login exitoso emite par de tokens
- **WHEN** la autenticación se completa satisfactoriamente
- **THEN** el sistema emite un access token y un refresh token válidos

#### Scenario: Refresh rota la sesión
- **WHEN** un cliente presenta un refresh token válido y no revocado
- **THEN** el sistema invalida ese refresh token
- **AND** emite un nuevo access token y un nuevo refresh token

#### Scenario: Reuso de refresh token invalidado
- **WHEN** un cliente intenta reutilizar un refresh token ya rotado o revocado
- **THEN** el sistema rechaza la operación y no emite nuevos tokens

### Requirement: Logout revoca la sesión

El sistema SHALL permitir cerrar sesión revocando el refresh token o la sesión asociada para impedir usos posteriores.

#### Scenario: Logout invalida refresh token
- **WHEN** un usuario autenticado solicita cerrar sesión
- **THEN** el sistema revoca el refresh token o sesión correspondiente

### Requirement: Identidad y tenant derivados solo del JWT verificado

El sistema SHALL resolver identidad, tenant y roles exclusivamente desde el JWT verificado y datos server-side asociados. Ningún parámetro de la request SHALL alterar esa identidad.

#### Scenario: Dependency resuelve identidad desde sesión
- **WHEN** un endpoint protegido invoca `get_current_user` con un JWT válido
- **THEN** la dependency devuelve el usuario autenticado con su tenant y roles asociados

#### Scenario: Parámetros de request no alteran identidad
- **WHEN** la request contiene `user_id`, `tenant_id` u otros identificadores inconsistentes con el JWT
- **THEN** el sistema mantiene como identidad efectiva únicamente la derivada del token verificado
