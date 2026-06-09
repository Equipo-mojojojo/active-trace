## ADDED Requirements

### Requirement: Guard de autenticación (AuthGuard)
El sistema SHALL proveer un componente `AuthGuard` que envuelva las rutas protegidas. Si el usuario no está autenticado, SHALL redirigir a `/login` preservando la ruta de destino como `?next=` para volver tras el login. Si está autenticado, renderiza la ruta normalmente.

#### Scenario: Usuario no autenticado intenta acceder a ruta protegida
- **WHEN** el usuario no tiene sesión e intenta navegar a `/dashboard`
- **THEN** la app redirige a `/login?next=/dashboard` sin renderizar el contenido protegido

#### Scenario: Usuario autenticado accede a ruta protegida
- **WHEN** el usuario tiene sesión válida y navega a `/dashboard`
- **THEN** la app renderiza el contenido de `/dashboard` sin redirección

#### Scenario: Redirección post-login al destino original
- **WHEN** el usuario se autentica exitosamente con `?next=/calificaciones`
- **THEN** la app redirige a `/calificaciones` en lugar de al dashboard genérico

### Requirement: Guard de permisos (PermissionGuard)
El sistema SHALL proveer un componente `PermissionGuard` que recibe un permiso requerido (ej: `"liquidaciones:ver"`) y verifica si el usuario autenticado lo tiene. Si no lo tiene, redirige a `/403`. Si no hay sesión, el `AuthGuard` actúa primero.

#### Scenario: Usuario sin el permiso requerido
- **WHEN** un usuario PROFESOR intenta acceder a una ruta que requiere `"liquidaciones:ver"`
- **THEN** la app redirige a `/403` (Acceso denegado)

#### Scenario: Usuario con el permiso requerido
- **WHEN** un usuario FINANZAS accede a una ruta que requiere `"liquidaciones:ver"`
- **THEN** la app renderiza el contenido correctamente

#### Scenario: Página /403 visible y con link de regreso
- **WHEN** el usuario llega a `/403`
- **THEN** ve un mensaje "No tenés permiso para ver esta página" con un botón para volver al dashboard

### Requirement: Layout raíz con menú dinámico por permisos
El sistema SHALL proveer un `AppLayout` que envuelva todas las rutas protegidas. El menú de navegación SHALL mostrar solo las secciones a las que el usuario tiene acceso según sus permisos (`modulo:ver` o equivalente). El layout SHALL incluir nombre del usuario, tenant activo y botón de logout.

#### Scenario: Menú filtrado según permisos del usuario
- **WHEN** un usuario PROFESOR inicia sesión (sin permiso `"liquidaciones:ver"` ni `"auditoria:ver"`)
- **THEN** el menú NO muestra las secciones de Finanzas ni Auditoría

#### Scenario: Menú completo para ADMIN
- **WHEN** un usuario ADMIN inicia sesión
- **THEN** el menú muestra todas las secciones disponibles en el sistema

#### Scenario: Header muestra nombre y tenant
- **WHEN** el usuario está en cualquier pantalla protegida
- **THEN** el header/sidebar muestra el nombre del usuario y el nombre de la institución (tenant)

### Requirement: Rutas públicas (no requieren sesión)
El sistema SHALL diferenciar rutas públicas (`/login`, `/auth/2fa`, `/auth/forgot-password`, `/auth/reset-password`) de rutas protegidas. Las rutas públicas son accesibles sin sesión. Si un usuario autenticado navega a `/login`, SHALL redirigir al dashboard.

#### Scenario: Usuario autenticado visita /login
- **WHEN** el usuario con sesión activa navega a `/login`
- **THEN** la app redirige a `/dashboard` automáticamente

#### Scenario: Ruta no encontrada
- **WHEN** el usuario navega a una ruta que no existe (ej: `/ruta-inexistente`)
- **THEN** se renderiza una página 404 con link al dashboard (si autenticado) o a /login (si no autenticado)

---

### Requirement: Rutas del módulo profesor
El sistema SHALL registrar en el router las rutas del módulo de gestión de comisión para el PROFESOR, todas bajo `AppLayout` y protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta lista de comisiones
- **WHEN** el usuario navega a `/profesor/comisiones`
- **THEN** el router renderiza `MisComisionesPage` dentro de `AppLayout`, previa verificación de autenticación y permiso `atrasados:ver`

#### Scenario: Ruta detalle de comisión
- **WHEN** el usuario navega a `/profesor/comisiones/:comisionId`
- **THEN** el router renderiza `ComisionPage` con los tabs de análisis

#### Scenario: Ruta importación de calificaciones
- **WHEN** el usuario navega a `/profesor/comisiones/:comisionId/importar`
- **THEN** el router renderiza `ImportarCalificacionesPage`, con guard adicional de permiso `calificaciones:importar`

#### Scenario: Ruta comunicación a atrasados
- **WHEN** el usuario navega a `/profesor/comunicacion/:comisionId`
- **THEN** el router renderiza `ComunicacionPage` con guard de permiso `comunicacion:enviar`

#### Scenario: Ruta tracking de comunicaciones
- **WHEN** el usuario navega a `/profesor/comunicacion/tracking`
- **THEN** el router renderiza `TrackingComunicacionesPage` con guard de permiso `comunicacion:enviar`

#### Scenario: Ruta monitor de seguimiento
- **WHEN** el usuario navega a `/monitor`
- **THEN** el router renderiza `MonitorDocentePage` dentro de `AppLayout`, con guard de permiso `atrasados:ver`

---

### Requirement: Rutas del módulo de coordinación
El sistema SHALL registrar en el router las rutas del módulo de coordinación para COORDINADOR/ADMIN, todas bajo `AppLayout` y protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta dashboard de coordinación
- **WHEN** el usuario navega a `/coordinacion`
- **THEN** el router renderiza `CoordinacionDashboardPage` dentro de `AppLayout`, con guard de permiso `equipos:asignar`

#### Scenario: Ruta gestión de equipos
- **WHEN** el usuario navega a `/coordinacion/equipos`
- **THEN** el router renderiza `EquiposPage` con guard de permiso `equipos:asignar`

#### Scenario: Ruta gestión de avisos
- **WHEN** el usuario navega a `/coordinacion/avisos`
- **THEN** el router renderiza `AvisosPage` con guard de permiso `avisos:publicar`

#### Scenario: Ruta workflow de tareas
- **WHEN** el usuario navega a `/coordinacion/tareas`
- **THEN** el router renderiza `TareasPage` con guard de permiso `tareas:gestionar`

#### Scenario: Ruta monitor institucional
- **WHEN** el usuario navega a `/coordinacion/monitor`
- **THEN** el router renderiza `MonitorCoordinacionPage` con guard de permiso `atrasados:ver`

### Requirement: Rutas del módulo de encuentros
El sistema SHALL registrar en el router las rutas del módulo de encuentros bajo `AppLayout`, protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta lista de encuentros
- **WHEN** el usuario navega a `/encuentros`
- **THEN** el router renderiza `EncuentrosPage` dentro de `AppLayout`, con guard de permiso `encuentros:gestionar`

#### Scenario: Ruta guardias
- **WHEN** el usuario navega a `/encuentros/guardias`
- **THEN** el router renderiza `GuardiasPage` con guard de permiso `encuentros:gestionar`

### Requirement: Rutas del módulo de coloquios
El sistema SHALL registrar en el router las rutas del módulo de coloquios bajo `AppLayout`, protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta gestión de coloquios
- **WHEN** el usuario navega a `/coloquios`
- **THEN** el router renderiza `ColoquiosPage` dentro de `AppLayout`, con guard de permiso `equipos:asignar`

### Requirement: Menú dinámico actualizado con secciones de coordinación
El sistema SHALL actualizar el menú del `AppLayout` para incluir las nuevas secciones de coordinación, visibles solo para los usuarios con los permisos correspondientes.

#### Scenario: Menú muestra sección Coordinación para COORDINADOR
- **WHEN** un usuario con permiso `equipos:asignar` inicia sesión
- **THEN** el menú lateral muestra la sección "Coordinación" con sus sub-items (Equipos, Avisos, Tareas, Monitor)

#### Scenario: Menú muestra Encuentros y Coloquios para COORDINADOR
- **WHEN** un usuario con permiso `encuentros:gestionar` inicia sesión
- **THEN** el menú lateral muestra los ítems "Encuentros" y "Coloquios"

#### Scenario: PROFESOR no ve las secciones de coordinación
- **WHEN** un usuario PROFESOR (sin `equipos:asignar`) inicia sesión
- **THEN** el menú lateral NO muestra la sección "Coordinación"

---

### Requirement: Rutas del módulo de finanzas
El sistema SHALL registrar en el router las rutas del módulo de finanzas para el rol FINANZAS, todas bajo `AppLayout` y protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta panel de liquidaciones
- **WHEN** el usuario navega a `/finanzas/liquidaciones`
- **THEN** el router renderiza `LiquidacionesPage` dentro de `AppLayout`, previa verificación de autenticación y permiso `liquidaciones:ver`

#### Scenario: Ruta historial de liquidaciones
- **WHEN** el usuario navega a `/finanzas/liquidaciones/historial`
- **THEN** el router renderiza `HistorialLiquidacionesPage` con guard de permiso `liquidaciones:ver`

#### Scenario: Ruta grilla salarial
- **WHEN** el usuario navega a `/finanzas/grilla-salarial`
- **THEN** el router renderiza `GrillaSalarialPage` con guard de permiso `liquidaciones:configurar-salarios`

#### Scenario: Ruta facturas
- **WHEN** el usuario navega a `/finanzas/facturas`
- **THEN** el router renderiza `FacturasPage` con guard de permiso `facturas:ver`

#### Scenario: Acceso sin permiso de finanzas
- **WHEN** un usuario sin `liquidaciones:ver` navega a `/finanzas/liquidaciones`
- **THEN** el router redirige a `/403`

### Requirement: Rutas del módulo de administración
El sistema SHALL registrar en el router las rutas del módulo de administración para el rol ADMIN, todas bajo `AppLayout` y protegidas por `AuthGuard` + `PermissionGuard`.

#### Scenario: Ruta estructura académica
- **WHEN** el usuario navega a `/admin/estructura`
- **THEN** el router renderiza `EstructuraAcademicaPage` dentro de `AppLayout`, con guard de permiso `estructura:gestionar`

#### Scenario: Ruta gestión de usuarios
- **WHEN** el usuario navega a `/admin/usuarios`
- **THEN** el router renderiza `UsuariosPage` con guard de permiso `usuarios:gestionar`

#### Scenario: Ruta panel de auditoría
- **WHEN** el usuario navega a `/admin/auditoria`
- **THEN** el router renderiza `AuditoriaPage` con guard que acepta `auditoria:ver` o `auditoria:ver:propio`

#### Scenario: Acceso sin permiso de administración
- **WHEN** un usuario sin `estructura:gestionar` navega a `/admin/estructura`
- **THEN** el router redirige a `/403`

### Requirement: Menú dinámico — secciones Finanzas y Administración
El sistema SHALL mostrar en el menú las secciones de Finanzas y Administración según permisos del usuario.

#### Scenario: Menú muestra sección Finanzas para FINANZAS
- **WHEN** un usuario con permiso `liquidaciones:ver` inicia sesión
- **THEN** el menú lateral muestra la sección "Finanzas" con sus sub-items (Liquidaciones, Grilla salarial, Facturas)

#### Scenario: Menú muestra sección Administración para ADMIN
- **WHEN** un usuario con permiso `estructura:gestionar` o `usuarios:gestionar` o `auditoria:ver` inicia sesión
- **THEN** el menú lateral muestra la sección "Administración" con sus sub-items según los permisos

#### Scenario: FINANZAS no ve la sección de Administración
- **WHEN** un usuario FINANZAS (sin `estructura:gestionar`, `usuarios:gestionar` ni `auditoria:ver`) inicia sesión
- **THEN** el menú lateral NO muestra la sección "Administración"

#### Scenario: Menú completo para ADMIN
- **WHEN** un usuario ADMIN inicia sesión
- **THEN** el menú muestra todas las secciones disponibles en el sistema
