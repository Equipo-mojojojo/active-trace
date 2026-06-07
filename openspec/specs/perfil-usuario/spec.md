## ADDED Requirements

### Requirement: Ver perfil propio
El sistema SHALL exponer via `GET /api/perfil` el perfil completo del usuario autenticado, incluyendo campos PII (cifrados en reposo) y el campo `cuil` como solo lectura.

#### Scenario: Obtener perfil propio exitosamente
- **WHEN** cualquier usuario autenticado hace GET a `/api/perfil`
- **THEN** el sistema retorna 200 con todos los campos del perfil incluyendo `nombre`, `apellidos`, `email`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `modalidad_cobro`
- **AND** `cuil` está presente pero marcado como campo de solo lectura en la respuesta

#### Scenario: Sin autenticación retorna 401
- **WHEN** una petición no autenticada llega a `GET /api/perfil`
- **THEN** el sistema retorna 401 Unauthorized

### Requirement: Editar perfil propio (campos editables)
El sistema SHALL permitir a cualquier usuario autenticado actualizar sus campos editables via `PATCH /api/perfil`. Los campos editables son: `nombre`, `apellidos`, `banco`, `cbu`, `alias_cbu`, `regional`, `legajo_profesional`, `facturador`, `modalidad_cobro`. El campo `cuil` es inmutable para el usuario.

#### Scenario: Actualizar campo editable exitosamente
- **WHEN** un usuario autenticado hace PATCH a `/api/perfil` con `{"banco": "Banco Nación"}`
- **THEN** el sistema retorna 200 con el perfil actualizado incluyendo el nuevo valor de `banco`

#### Scenario: Intentar modificar cuil es rechazado
- **WHEN** un usuario hace PATCH a `/api/perfil` con `{"cuil": "20-12345678-1"}`
- **THEN** el sistema retorna 422 Unprocessable Entity indicando que `cuil` no es editable
- **AND** no se persiste ningún cambio en `cuil`

#### Scenario: Actualizar modalidad_cobro a factura
- **WHEN** un usuario hace PATCH a `/api/perfil` con `{"modalidad_cobro": "factura"}`
- **THEN** el sistema retorna 200 y el usuario queda marcado como facturante

#### Scenario: Aislamiento — usuario solo edita su propio perfil
- **WHEN** el usuario autenticado hace PATCH a `/api/perfil`
- **THEN** el sistema actualiza exclusivamente el registro del usuario de la sesión, no permite modificar otros usuarios

#### Scenario: PATCH con cuerpo vacío no modifica nada
- **WHEN** un usuario hace PATCH a `/api/perfil` con `{}`
- **THEN** el sistema retorna 200 con el perfil sin cambios
