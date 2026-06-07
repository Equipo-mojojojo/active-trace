## ADDED Requirements

### Requirement: Calcular liquidación del período (RN-21)
El sistema SHALL calcular la liquidación de honorarios de cada docente activo para un período dado. El cálculo es: `total = monto_base + monto_plus`, donde `monto_base` es el `SalarioBase` vigente para el rol del docente en ese período, y `monto_plus` es la suma de los `SalarioPlus` vigentes de cada comisión activa del docente que tenga `grupo_plus_clave` no nulo, respetando el `tope_plus` del tenant si está definido.

#### Scenario: Calcular liquidación con base y plus
- **WHEN** FINANZAS solicita la liquidación del período `2026-05` para un docente con rol PROFESOR y 2 comisiones activas con `grupo_plus_clave`
- **THEN** el sistema retorna `monto_base = SalarioBase vigente(PROFESOR, 2026-05)` y `monto_plus = SalarioPlus(grupo1, PROFESOR) + SalarioPlus(grupo2, PROFESOR)`
- **AND** `total = monto_base + monto_plus`

#### Scenario: Calcular liquidación sin comisiones con plus
- **WHEN** un docente tiene comisiones activas pero todas con `grupo_plus_clave` nulo
- **THEN** `monto_plus = 0` y `total = monto_base`

#### Scenario: Respetar tope_plus del tenant
- **WHEN** `Tenant.tope_plus = 2` y el docente tiene 5 comisiones con `grupo_plus_clave`
- **THEN** solo se suman los plus de las primeras 2 comisiones
- **AND** `monto_plus` refleja exactamente 2 plus acumulados

#### Scenario: Plus sin SalarioPlus vigente en el período
- **WHEN** la comisión de un docente tiene `grupo_plus_clave = "PROG"` pero no existe SalarioPlus vigente para `(PROG, rol)` en el período
- **THEN** el plus de esa comisión se computa como 0 (no bloquea el cálculo)

#### Scenario: Aislamiento multi-tenant en cálculo
- **WHEN** se calcula la liquidación de un docente
- **THEN** solo se usan datos de salario y plus del mismo tenant del docente

### Requirement: Vista de liquidaciones del período (F10.1 / F10.6)
El sistema SHALL exponer via GET `/api/liquidaciones/` la lista de liquidaciones del período seleccionado, segmentadas en tres grupos: General (PROFESOR, TUTOR, COORDINADOR sin factura), NEXO, y Docentes-que-facturan. La respuesta SHALL incluir KPIs de cabecera: `total_sin_factura` y `total_con_factura`.

#### Scenario: Listar liquidaciones con segmentación
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/?periodo=2026-05`
- **THEN** el sistema retorna 200 con tres segmentos: `general`, `nexo`, `facturantes`
- **AND** incluye KPIs `total_sin_factura` y `total_con_factura`

#### Scenario: Filtrar liquidaciones por docente
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/?periodo=2026-05&usuario_id={id}`
- **THEN** el sistema retorna solo la liquidación de ese docente en el período

#### Scenario: Acceso sin permiso liquidaciones:ver
- **WHEN** un usuario sin `liquidaciones:ver` accede a `/api/liquidaciones/`
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Cerrar liquidación del período (RN-22)
El sistema SHALL permitir a FINANZAS cerrar la liquidación de un período via POST `/api/liquidaciones/{periodo}/cerrar`. Una liquidación cerrada es **inmutable**: no puede modificarse ni reabrirse. El cierre genera un evento de auditoría `LIQUIDACION_CERRAR`.

#### Scenario: Cerrar liquidación abierta exitosamente
- **WHEN** FINANZAS hace POST a `/api/liquidaciones/2026-05/cerrar`
- **THEN** el sistema cambia `estado = Cerrada` para todas las liquidaciones del período
- **AND** registra un evento `LIQUIDACION_CERRAR` en `AuditLog` con `usuario_id` y `tenant_id`
- **AND** retorna 200 OK

#### Scenario: Intentar modificar liquidación cerrada
- **WHEN** se intenta actualizar cualquier campo de una liquidación con `estado = Cerrada`
- **THEN** el sistema retorna 409 Conflict con mensaje "liquidacion_cerrada"
- **AND** no persiste ningún cambio

#### Scenario: Cerrar liquidación ya cerrada
- **WHEN** FINANZAS intenta cerrar un período ya cerrado
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Acceso sin permiso liquidaciones:cerrar
- **WHEN** un usuario sin `liquidaciones:cerrar` intenta cerrar
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Historial de liquidaciones cerradas (F10.3)
El sistema SHALL exponer via GET `/api/liquidaciones/historial` el listado de períodos con liquidaciones cerradas para consulta y auditoría.

#### Scenario: Listar períodos cerrados
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/historial`
- **THEN** el sistema retorna 200 con la lista de períodos cerrados, ordenados por `periodo` descendente

#### Scenario: Ver detalle de período cerrado
- **WHEN** FINANZAS hace GET a `/api/liquidaciones/historial?periodo=2026-04`
- **THEN** el sistema retorna la liquidación cerrada del período con todos sus campos incluido `total`
