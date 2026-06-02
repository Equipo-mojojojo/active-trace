## Context

Con C-01 y C-02 ya existe el esqueleto técnico, la base de persistencia multi-tenant, el cifrado en reposo y el aislamiento por `tenant_id`. El siguiente cimiento crítico es la autenticación: el sistema necesita emitir sesiones confiables, derivar identidad y tenant exclusivamente desde JWT verificado, y endurecer el acceso anónimo con refresh rotation, recuperación segura y 2FA opcional.

Este change además prepara la dependencia principal de C-04: `get_current_user` debe existir antes de poder evaluar permisos finos por request. También debe respetar decisiones ya cerradas del producto: auth propio, JWT de vida corta, refresh token con rotación, 2FA TOTP opcional y fail-closed ante cualquier ambigüedad de identidad.

## Goals / Non-Goals

**Goals:**
- Implementar login con email + password hasheado con Argon2id y emisión de JWT access + refresh con rotación.
- Introducir `get_current_user` como dependency canónica para resolver identidad, tenant y roles desde la sesión verificada.
- Incorporar 2FA TOTP opcional por usuario sin emitir sesión final hasta completar el segundo factor.
- Incorporar recuperación de password con token de un solo uso y expiración corta.
- Aplicar rate limiting a login por IP+email y restringir el acceso anónimo solo a rutas de auth.
- Dejar el modelo listo para que C-04 resuelva permisos server-side sobre una identidad autenticada estable.

**Non-Goals:**
- Implementar la matriz completa rol × permiso ni `require_permission` (C-04).
- Implementar impersonación auditada (C-05 / módulo de auditoría).
- Resolver SSO federado con Moodle; C-03 sigue ADR-001 de auth propio.
- Implementar UX frontend completa; este change se enfoca en contratos backend, sesión y seguridad.

## Decisions

### D1 — Auth propio con sesión corta + refresh rotation

La sesión se compondrá de un access token JWT de corta duración y un refresh token persistido con rotación: cada uso invalida el refresh anterior y emite uno nuevo.

**Por qué:** minimiza el impacto de filtración de access token y permite revocar sesiones por logout o reuso indebido.

**Alternativa descartada:** access token largo sin refresh rotation. Se descarta por débil frente a robo de token y porque contradice el contrato del producto.

### D2 — Identity-first: `get_current_user` resuelve todo desde JWT verificado

La identity dependency decodifica y valida el JWT, recupera al usuario y resuelve tenant/roles desde datos confiables del servidor. Ningún header, body ni query param puede redefinir identidad.

**Por qué:** materializa la regla de oro de seguridad y evita ataques de suplantación por parámetros.

**Alternativa descartada:** aceptar `tenant_id` o `user_id` desde request para “optimizar” resolución. Se descarta por inseguro y contrario a la arquitectura del producto.

### D3 — 2FA TOTP como segundo paso de la autenticación, no como sesión separada

Las credenciales válidas no emiten la sesión final si el usuario tiene 2FA habilitado; primero se emite un estado transitorio o challenge de auth pendiente que requiere un TOTP válido.

**Por qué:** evita sesiones parcialmente autenticadas y mantiene un flujo claro: credenciales → challenge 2FA → sesión final.

**Alternativa descartada:** emitir sesión completa antes de validar TOTP y degradar permisos. Se descarta porque rompe el modelo de seguridad y complejiza el enforcement.

### D4 — Tokens sensibles persistidos de forma segura y revocables

Refresh tokens y tokens de recuperación deberán persistirse en una forma segura/revocable (hash o equivalente), con expiración y estado de uso/revocación. Los secretos TOTP del usuario se almacenarán cifrados en reposo reutilizando la infraestructura de C-02.

**Por qué:** evita almacenar secretos reutilizables en texto plano y hace posible detectar reuso, logout y expiración.

**Alternativa descartada:** refresh tokens opacos guardados en claro. Se descarta por exposición innecesaria ante filtraciones de base.

### D5 — Rate limiting persistente o compartido a nivel backend

El login aplicará limitación de intentos por combinación IP+email en ventana corta (`5/60s`), con enforcement server-side compatible con múltiples instancias.

**Por qué:** el acceso anónimo es la superficie más expuesta del sistema; el rate limit reduce fuerza bruta y credential stuffing.

**Alternativa descartada:** rate limit solo en memoria de proceso sin coordinación. Se descarta porque en despliegues multi-instancia sería inconsistente.

## Risks / Trade-offs

- **[Riesgo: modelado de auth invade demasiado RBAC]** → Mitigación: limitar C-03 a identidad, sesión y claims mínimos; dejar permisos finos para C-04.
- **[Riesgo: 2FA añade complejidad al flujo de login]** → Mitigación: separar claramente challenge transitorio de sesión final y cubrirlo con tests de flujo completo.
- **[Riesgo: refresh rotation mal implementada deja reuso silencioso]** → Mitigación: persistir estado de revocación/uso y testear explícitamente el reuso inválido.
- **[Trade-off: más tablas y estados operativos de auth]** → Mitigación: mantener el modelo mínimo: usuario, refresh session/token, reset token y configuración TOTP.

## Migration Plan

1. Agregar modelos/tablas de usuario autenticable, refresh tokens/sesiones, recuperación de password y 2FA.
2. Extender configuración y secretos operativos de auth.
3. Implementar servicios y repositories de autenticación.
4. Exponer endpoints públicos de auth y dependency `get_current_user`.
5. Ejecutar tests de login, refresh rotation, 2FA, recovery, rate limiting e identidad inmutable.

**Rollback:** revertir las migraciones de auth y desactivar los endpoints públicos. Como todavía no existirán flujos dependientes de negocio aguas arriba, el rollback sigue siendo manejable en esta etapa temprana.

## Open Questions

- ¿El rate limiting se implementará inicialmente con almacenamiento en DB o con una store compartida más liviana? El contrato exige el comportamiento, pero la estrategia operativa concreta puede variar.
- ¿Conviene que el challenge transitorio de 2FA use un token firmado de vida ultracorta o una tabla efímera persistida para simplificar revocación y trazabilidad?
