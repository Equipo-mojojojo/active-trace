## ADDED Requirements

### Requirement: Lista de facturas de docentes con filtros
El sistema SHALL mostrar en `FacturasPage` (ruta `/finanzas/facturas`) una tabla de comprobantes (`GET /api/facturas/`) con columnas: fecha de carga, docente, período, detalle, monto, archivo adjunto (indicador), estado (badge: Pendiente en ámbar, Abonada en verde) y acciones. SHALL proveer filtros de docente, estado (pendiente/abonada), rango de fechas y búsqueda libre.

#### Scenario: Listar facturas
- **WHEN** un usuario con `facturas:ver` navega a `/finanzas/facturas`
- **THEN** ve la tabla de comprobantes del tenant con sus estados

#### Scenario: Filtrar por estado y período
- **WHEN** el usuario selecciona estado "pendiente" y un período
- **THEN** la tabla re-consulta `GET /api/facturas/?estado=pendiente&periodo=...` y muestra solo las coincidencias

#### Scenario: Badge de estado por color
- **WHEN** una factura tiene estado "abonada"
- **THEN** su badge se muestra en verde; las "pendiente" se muestran en ámbar

### Requirement: Crear factura de docente facturante
El sistema SHALL proveer un botón "Nueva factura" que abra un formulario para crear un comprobante (`POST /api/facturas/`) con `usuario_id`, `periodo`, `monto`, `detalle`, `fecha_carga`. Tras éxito, SHALL cerrar el formulario e invalidar la lista.

#### Scenario: Crear factura exitosamente
- **WHEN** el usuario completa el formulario de nueva factura y guarda
- **THEN** se hace POST, la factura se crea con estado "pendiente" y la lista se actualiza

#### Scenario: Rechazo de docente no facturante
- **WHEN** el backend responde 422 (docente no facturante)
- **THEN** el formulario muestra el mensaje de error sin cerrar ni descartar los datos

### Requirement: Cambiar estado de factura
El sistema SHALL permitir cambiar el estado de una factura entre pendiente y abonada via `PATCH /api/facturas/{id}/estado`. Tras éxito, SHALL invalidar la lista.

#### Scenario: Marcar factura como abonada
- **WHEN** el usuario hace click en "Cambiar estado" y confirma "abonada"
- **THEN** se hace PATCH y la fila refleja el nuevo estado con su badge verde

### Requirement: Adjuntar archivo a factura
El sistema SHALL permitir adjuntar un archivo a una factura via `PUT /api/facturas/{id}/archivo` enviando `FormData` (multipart). SHALL mostrar el indicador de adjunto cuando la factura tiene `archivo_path`.

#### Scenario: Adjuntar archivo
- **WHEN** el usuario selecciona un archivo y lo sube en una factura existente
- **THEN** se hace PUT con FormData y la fila muestra el indicador de archivo adjunto tras éxito

### Requirement: Protección de acceso a facturas
La ruta `/finanzas/facturas` SHALL estar protegida por `AuthGuard` + `PermissionGuard` con permiso `facturas:ver`. Las acciones de creación y cambio de estado SHALL requerir `facturas:gestionar`; los controles correspondientes se ocultan sin ese permiso.

#### Scenario: Acceso solo lectura sin facturas:gestionar
- **WHEN** un usuario con `facturas:ver` pero sin `facturas:gestionar` abre la página
- **THEN** ve la tabla pero no los botones de crear ni cambiar estado

#### Scenario: Acceso sin facturas:ver
- **WHEN** un usuario sin `facturas:ver` navega a `/finanzas/facturas`
- **THEN** la app redirige a `/403`
