## 1. Modelo y configuración de autenticación

- [x] 1.1 Definir/extender modelos persistentes de usuario autenticable, refresh session/token, recovery token y estado/configuración de 2FA
- [x] 1.2 Crear las migraciones Alembic necesarias para auth propio sin invadir RBAC de C-04
- [x] 1.3 Extender `Settings` y `.env.example` con variables operativas de auth, expiraciones y secretos auxiliares

## 2. Login, JWT y resolución de identidad

- [x] 2.1 Implementar hashing/verificación de password con Argon2id para credenciales de usuario
- [x] 2.2 Implementar emisión de access token JWT con claims mínimos (`sub`, `tenant_id`, `roles`, `exp`)
- [x] 2.3 Implementar `get_current_user` para resolver identidad, tenant y roles exclusivamente desde el JWT verificado
- [x] 2.4 Escribir tests de login exitoso/fallido y de identidad inmutable frente a parámetros de request

## 3. Refresh rotation y logout

- [x] 3.1 Implementar persistencia y rotación de refresh tokens con revocación por reuso
- [x] 3.2 Implementar `POST /api/auth/refresh` y `POST /api/auth/logout`
- [x] 3.3 Escribir tests que validen refresh exitoso, reuso inválido y logout con revocación efectiva

## 4. Recuperación de password

- [x] 4.1 Implementar `POST /api/auth/forgot` generando token de un solo uso con expiración corta
- [x] 4.2 Implementar `POST /api/auth/reset` consumiendo el token, actualizando password e invalidando reuso
- [x] 4.3 Escribir tests de recuperación exitosa, token vencido y token reutilizado

## 5. 2FA TOTP

- [x] 5.1 Implementar enrolamiento y almacenamiento seguro del secreto TOTP por usuario
- [x] 5.2 Implementar el challenge/validación TOTP dentro del flujo de login antes de emitir la sesión final
- [x] 5.3 Escribir tests del flujo 2FA: enrolamiento, login con challenge, código inválido y autenticación final exitosa

## 6. Hardening del acceso anónimo

- [x] 6.1 Implementar rate limiting de login por combinación IP+email (`5/60s`)
- [x] 6.2 Verificar que solo login/forgot/reset sean accesibles sin sesión y que el resto de rutas exijan autenticación válida
- [x] 6.3 Escribir tests de rate limiting y de restricción de acceso anónimo fuera del flujo de auth

## 7. Validación final y readiness para C-04

- [x] 7.1 Ejecutar la suite completa de C-03 contra DB real de test y confirmar verde
- [x] 7.2 Verificar que los claims del JWT no contengan permisos y que la resolución final siga siendo server-side
- [x] 7.3 Confirmar que C-03 deja listo el terreno para C-04 (`require_permission`) sin mezclar todavía RBAC fino en este change
