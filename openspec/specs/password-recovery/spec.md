## ADDED Requirements

### Requirement: Recuperación de password con token de un solo uso

El sistema SHALL permitir solicitar recuperación de password mediante un token de un solo uso, con expiración corta, asociado al usuario solicitante.

#### Scenario: Solicitud de recuperación genera token
- **WHEN** un usuario solicita recuperar su password con un email registrado
- **THEN** el sistema genera un token de recuperación de un solo uso con expiración

### Requirement: Reset invalida token tras uso o vencimiento

El sistema SHALL invalidar el token de recuperación una vez utilizado o cuando expire, impidiendo su reutilización.

#### Scenario: Reset exitoso consume token
- **WHEN** el usuario presenta un token válido y define un nuevo password válido
- **THEN** el sistema actualiza el password
- **AND** invalida el token usado

#### Scenario: Token vencido o reutilizado se rechaza
- **WHEN** un usuario intenta usar un token expirado o ya consumido
- **THEN** el sistema rechaza el reset y no modifica la credencial
