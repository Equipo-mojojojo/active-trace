## ADDED Requirements

### Requirement: Rate limiting de login por IP y email

El sistema SHALL limitar los intentos de login a un máximo de 5 dentro de una ventana de 60 segundos por combinación de IP y email para mitigar fuerza bruta.

#### Scenario: Intentos exceden el límite permitido
- **WHEN** una misma combinación IP+email supera 5 intentos fallidos dentro de 60 segundos
- **THEN** el sistema rechaza temporalmente nuevos intentos de login para esa combinación

### Requirement: Acceso anónimo restringido al flujo de autenticación

El sistema SHALL permitir acceso sin sesión únicamente a las operaciones de login y recuperación de password; cualquier otro endpoint SHALL requerir autenticación válida.

#### Scenario: Endpoint no público exige sesión
- **WHEN** un cliente anónimo intenta acceder a un endpoint fuera del flujo de autenticación
- **THEN** el sistema rechaza la operación por falta de autenticación válida
