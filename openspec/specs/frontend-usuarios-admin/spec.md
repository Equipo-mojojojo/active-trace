## ADDED Requirements

### Requirement: Lista de usuarios del tenant
El sistema SHALL mostrar en `UsuariosPage` (ruta `/admin/usuarios`) una tabla de los usuarios del tenant con columnas: nombre, email, rol (badge de color por rol: ADMIN, COORDINADOR, PROFESOR, TUTOR, NEXO, FINANZAS), estado (Activo verde / Inactivo gris) y acciones. SHALL proveer búsqueda y filtro por rol.

#### Scenario: Listar usuarios
- **WHEN** un usuario con `usuarios:gestionar` navega a `/admin/usuarios`
- **THEN** ve la tabla de usuarios del tenant con su rol y estado

#### Scenario: Filtrar por rol
- **WHEN** el usuario selecciona un rol en el filtro
- **THEN** la tabla muestra solo los usuarios con ese rol

#### Scenario: Búsqueda libre
- **WHEN** el usuario escribe en el buscador
- **THEN** la tabla filtra por nombre o email coincidente

### Requirement: Crear y editar usuario en drawer
El sistema SHALL proveer un botón "Nuevo usuario" y una acción "Editar" por fila que abran un drawer lateral con campos: nombre, email, multi-select de roles (chips) y toggle de estado activo. Al guardar con éxito, SHALL cerrar el drawer e invalidar la lista.

#### Scenario: Abrir drawer para nuevo usuario
- **WHEN** el usuario hace click en "Nuevo usuario"
- **THEN** se abre el drawer con el formulario vacío

#### Scenario: Abrir drawer para editar usuario existente
- **WHEN** el usuario hace click en "Editar" en una fila
- **THEN** se abre el drawer con los datos del usuario precargados, incluyendo sus roles como chips

#### Scenario: Guardar usuario exitosamente
- **WHEN** el usuario completa el formulario y guarda
- **THEN** se persiste en el backend, el drawer se cierra y la tabla se actualiza

#### Scenario: Validación de campos obligatorios
- **WHEN** el usuario intenta guardar sin nombre o sin email
- **THEN** el formulario muestra errores en los campos vacíos y no envía la request

### Requirement: Asignación de roles al usuario
El sistema SHALL permitir asignar uno o más roles a un usuario mediante el multi-select de roles del drawer. La identidad y el tenant del usuario que opera vienen siempre de la sesión; NUNCA se envían como parámetros desde la UI.

#### Scenario: Agregar y quitar roles
- **WHEN** el usuario selecciona y deselecciona roles en el multi-select y guarda
- **THEN** el usuario editado queda con exactamente el conjunto de roles seleccionado

### Requirement: Activar / desactivar usuario
El sistema SHALL permitir activar o desactivar un usuario mediante el toggle de estado del drawer (soft, sin hard delete).

#### Scenario: Desactivar usuario
- **WHEN** el usuario desactiva el toggle de estado y guarda
- **THEN** el usuario queda en estado "Inactivo" y su fila muestra el badge gris

### Requirement: Protección de acceso a usuarios
La ruta `/admin/usuarios` SHALL estar protegida por `AuthGuard` + `PermissionGuard` con permiso `usuarios:gestionar`.

#### Scenario: Acceso sin permiso
- **WHEN** un usuario sin `usuarios:gestionar` navega a `/admin/usuarios`
- **THEN** la app redirige a `/403`
