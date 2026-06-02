## Why

Con C-02 ya existe una base multi-tenant segura para persistencia, pero el sistema todavía no tiene una forma confiable de autenticar usuarios, emitir sesiones ni derivar identidad y tenant desde un contexto verificable. C-03 es crítico porque materializa la regla de oro de seguridad: quién es el usuario, a qué tenant pertenece y qué roles trae su sesión no pueden depender nunca de datos manipulables de la request.

## What Changes

- Incorporar autenticación propia con email + password hasheado con Argon2id y emisión de sesión basada en JWT de vida corta.
- Implementar refresh token con rotación e invalidación por reuso, incluyendo logout con revocación de sesión.
- Agregar soporte de 2FA TOTP opcional por usuario, como gate entre credenciales válidas y emisión final de sesión.
- Incorporar flujo de recuperación de contraseña con token de un solo uso y expiración corta.
- Definir `get_current_user` como dependency central para resolver identidad, tenant y roles exclusivamente desde el JWT verificado.
- Aplicar rate limiting de login por IP+email para endurecer el acceso anónimo.

## Capabilities

### New Capabilities
- `jwt-session-auth`: login, logout, access token corto, refresh token con rotación y resolución server-side de identidad desde la sesión.
- `two-factor-auth`: enrolamiento y verificación de TOTP opcional antes de emitir la sesión final.
- `password-recovery`: solicitud y confirmación de reset de password mediante token de un solo uso con expiración.
- `auth-rate-limiting`: limitación de intentos de login por IP+email para mitigar fuerza bruta.

### Modified Capabilities
- `app-configuration`: el contrato de configuración base se amplía para contemplar parámetros operativos de auth, expiración y secretos asociados a sesiones/recuperación.

## Impact

- Afecta `backend/app/core/`, `backend/app/models/`, `backend/app/repositories/`, `backend/app/services/`, `backend/app/api/v1/routers/` y nuevas migraciones Alembic.
- Introduce modelos y tablas de soporte para usuarios/sesiones/tokens de recuperación/2FA, además de endpoints públicos de autenticación.
- Prepara el terreno para C-04 (`rbac-permisos-finos`), que dependerá de `get_current_user` y de una sesión autenticada estable.
- Refuerza decisiones cerradas del producto: auth propio, JWT con refresh rotation, 2FA opcional, tenant e identidad derivados solo de la sesión verificada.
