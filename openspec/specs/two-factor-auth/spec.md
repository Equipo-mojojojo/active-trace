## ADDED Requirements

### Requirement: 2FA TOTP opcional por usuario

El sistema SHALL permitir habilitar 2FA basado en TOTP por usuario, de forma opcional, como segundo factor para la autenticación.

#### Scenario: Usuario habilita 2FA
- **WHEN** un usuario autenticado inicia el enrolamiento de 2FA
- **THEN** el sistema genera un secreto TOTP y material suficiente para completar la configuración

### Requirement: 2FA bloquea la emisión de sesión final hasta validación

El sistema SHALL exigir un código TOTP válido después de credenciales correctas y antes de emitir la sesión final cuando el usuario tenga 2FA habilitado.

#### Scenario: Credenciales válidas con 2FA habilitado requieren challenge adicional
- **WHEN** un usuario con 2FA activo ingresa email y password correctos
- **THEN** el sistema no emite la sesión final todavía
- **AND** exige un código TOTP válido para completar el login

#### Scenario: Código TOTP inválido impide autenticación final
- **WHEN** el usuario presenta un código TOTP inválido o expirado
- **THEN** el sistema rechaza el segundo factor
- **AND** no emite la sesión autenticada
