## ADDED Requirements

### Requirement: Login con email y contraseña
El sistema SHALL proveer una pantalla `/login` que acepte email y contraseña, valide el formulario client-side con Zod y envíe las credenciales al backend. Ante credenciales válidas, almacena el access token en memoria y redirige al dashboard. Ante error 401, muestra mensaje de error sin revelar cuál campo es incorrecto.

#### Scenario: Login exitoso sin 2FA
- **WHEN** el usuario ingresa credenciales correctas y el tenant no requiere 2FA
- **THEN** el access token se almacena en memoria, el estado de sesión se puebla con user/roles/permissions/tenant, y la app redirige a `/dashboard`

#### Scenario: Login exitoso con 2FA requerido
- **WHEN** el usuario ingresa credenciales correctas y el backend responde con `requires_2fa: true`
- **THEN** la app redirige a `/auth/2fa` con el estado parcial de auth (pre-sesión)

#### Scenario: Credenciales inválidas
- **WHEN** el usuario ingresa credenciales incorrectas (usuario no existe o contraseña incorrecta)
- **THEN** se muestra "Credenciales inválidas" sin indicar cuál campo falló, el formulario NO se limpia

#### Scenario: Validación client-side
- **WHEN** el usuario intenta enviar el formulario con email malformado o contraseña vacía
- **THEN** el error de validación aparece bajo el campo correspondiente sin llamar al backend

### Requirement: Autenticación de dos factores (2FA)
El sistema SHALL proveer una pantalla `/auth/2fa` que solicite el código TOTP. Si el código es válido, completa el flujo de auth. Si es inválido, muestra error. Solo es accesible cuando el backend exige 2FA en ese tenant.

#### Scenario: Código TOTP correcto
- **WHEN** el usuario ingresa un código TOTP válido de 6 dígitos
- **THEN** el backend emite el access token completo, la sesión se completa y la app redirige a `/dashboard`

#### Scenario: Código TOTP incorrecto
- **WHEN** el usuario ingresa un código incorrecto
- **THEN** se muestra "Código inválido o expirado" y el campo se limpia para reintento

#### Scenario: Acceso directo a /auth/2fa sin sesión parcial
- **WHEN** el usuario navega directamente a `/auth/2fa` sin pasar por el login
- **THEN** la app redirige a `/login`

### Requirement: Recuperación de contraseña
El sistema SHALL proveer un flujo de dos pantallas: (1) `/auth/forgot-password` donde el usuario ingresa su email para recibir un token; (2) `/auth/reset-password?token=...` donde establece la nueva contraseña. Ambas pantallas muestran confirmación genérica independientemente del resultado para no revelar si el email existe.

#### Scenario: Solicitud de recuperación enviada
- **WHEN** el usuario ingresa su email y envía el formulario de recuperación
- **THEN** la app muestra "Si tu email está registrado, recibirás las instrucciones en breve" (sin importar si el email existe)

#### Scenario: Reset de contraseña con token válido
- **WHEN** el usuario accede al enlace con token válido e ingresa una nueva contraseña
- **THEN** la contraseña se actualiza, el token queda invalidado y la app redirige a `/login` con mensaje de éxito

#### Scenario: Token inválido o expirado
- **WHEN** el usuario accede con un token inválido o expirado
- **THEN** se muestra "El enlace expiró o ya fue usado. Solicitá uno nuevo." con link a `/auth/forgot-password`

### Requirement: Logout
El sistema SHALL proveer una acción de logout que invoque `POST /auth/logout` en el backend (para invalidar el refresh token), limpie el estado de sesión en memoria y redirija a `/login`.

#### Scenario: Logout exitoso
- **WHEN** el usuario hace click en "Cerrar sesión"
- **THEN** se llama al backend, la sesión se limpia localmente y la app redirige a `/login`

#### Scenario: Logout ante fallo del backend
- **WHEN** el backend devuelve error en `/auth/logout`
- **THEN** la sesión se limpia localmente de todas formas y la app redirige a `/login` (fail-safe)

### Requirement: Restauración de sesión al iniciar la app
El sistema SHALL intentar restaurar la sesión al cargar la app ejecutando `POST /auth/refresh`. Si el refresh token es válido, la sesión se restaura sin que el usuario tenga que volver a hacer login. Si falla, el usuario ve `/login`.

#### Scenario: Refresh token válido al recargar la página
- **WHEN** el usuario recarga el browser con una sesión activa
- **THEN** la app ejecuta `/auth/refresh` al iniciar, obtiene un nuevo access token y restaura la sesión automáticamente

#### Scenario: Sin sesión activa al recargar
- **WHEN** el usuario recarga sin sesión o con refresh token expirado
- **THEN** `/auth/refresh` falla, la app muestra la pantalla de login
