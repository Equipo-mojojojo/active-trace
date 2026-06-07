## ADDED Requirements

### Requirement: Registrar y gestionar facturas de docentes que facturan (F10.5 / RN-35)
El sistema SHALL permitir a FINANZAS crear y gestionar comprobantes (`Factura`) emitidos por docentes con modalidad de cobro por facturación. Los docentes facturantes están marcados con `excluido_por_factura = true` en su `Liquidacion` y **no se incluyen** en el total de liquidación general.

#### Scenario: Crear factura de docente facturante
- **WHEN** FINANZAS hace POST a `/api/facturas/` con `usuario_id`, `periodo`, `monto`, `detalle`, `fecha_carga`
- **THEN** el sistema crea la factura con `estado = pendiente` y retorna 201 Created

#### Scenario: Rechazar factura de docente no facturante
- **WHEN** FINANZAS intenta crear una factura para un docente cuya modalidad de cobro no es facturación
- **THEN** el sistema retorna 422 Unprocessable Entity indicando que el docente no es facturante

#### Scenario: Listar facturas con filtros
- **WHEN** FINANZAS hace GET a `/api/facturas/?estado=pendiente&periodo=2026-05`
- **THEN** el sistema retorna 200 con la lista de facturas que coinciden con los filtros del tenant

#### Scenario: Marcar factura como abonada
- **WHEN** FINANZAS hace PATCH a `/api/facturas/{id}/estado` con `estado = abonada`
- **THEN** el sistema actualiza el estado y retorna 200 OK

#### Scenario: Exclusión de facturantes del total de liquidación general
- **WHEN** se calcula la liquidación del período
- **THEN** los docentes con `excluido_por_factura = true` aparecen en el segmento `facturantes`
- **AND** su monto NO se incluye en el KPI `total_sin_factura`
- **AND** su monto SÍ se incluye en el KPI `total_con_factura`

#### Scenario: Aislamiento multi-tenant en facturas
- **WHEN** FINANZAS del tenant A lista facturas
- **THEN** solo se retornan facturas del tenant A

### Requirement: Adjuntar archivo a factura
El sistema SHALL permitir adjuntar un archivo (PDF, imagen) a una factura via PUT `/api/facturas/{id}/archivo`. El sistema SHALL almacenar el path del archivo, no el contenido binario en la DB.

#### Scenario: Adjuntar archivo a factura existente
- **WHEN** FINANZAS hace PUT a `/api/facturas/{id}/archivo` con un archivo válido
- **THEN** el sistema guarda el `archivo_path` en el registro y retorna 200 OK

#### Scenario: Obtener factura con archivo adjunto
- **WHEN** FINANZAS hace GET a `/api/facturas/{id}`
- **THEN** el sistema retorna el registro con `archivo_path` no nulo si existe adjunto

### Requirement: Permisos de facturas
Los endpoints de facturas SHALL requerir `facturas:ver` para lectura y `facturas:gestionar` para creación y cambio de estado.

#### Scenario: Acceso de solo lectura con facturas:ver
- **WHEN** un usuario con `facturas:ver` pero sin `facturas:gestionar` hace GET a `/api/facturas/`
- **THEN** el sistema retorna 200 OK

#### Scenario: Intento de crear sin facturas:gestionar
- **WHEN** un usuario sin `facturas:gestionar` hace POST a `/api/facturas/`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Acceso sin autenticación
- **WHEN** una petición no autenticada llega a cualquier endpoint `/api/facturas/`
- **THEN** el sistema retorna 401 Unauthorized
