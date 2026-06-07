## ADDED Requirements

### Requirement: Aprobación humana puede ser obligatoria por tenant
El sistema SHALL permitir que cada tenant configure si los envíos masivos requieren aprobación humana antes del despacho.

#### Scenario: Tenant con aprobación obligatoria retiene el lote
- **WHEN** un tenant tiene activa la política de aprobación para comunicaciones masivas
- **THEN** las comunicaciones confirmadas no quedan elegibles para el worker hasta ser aprobadas

### Requirement: Aprobación y cancelación pueden ejecutarse por lote o individualmente
Un actor con permiso `comunicacion:aprobar` SHALL poder aprobar o cancelar un lote completo o comunicaciones individuales dentro del lote.

#### Scenario: Aprobador aprueba un lote completo
- **WHEN** un aprobador confirma la aprobación de un lote pendiente
- **THEN** todas las comunicaciones elegibles de ese lote quedan habilitadas para el worker

#### Scenario: Aprobador cancela una comunicación individual
- **WHEN** un aprobador cancela solo una comunicación de un lote pendiente
- **THEN** esa comunicación pasa a `Cancelado` y el resto del lote conserva su estado previo

### Requirement: Acciones de aprobación generan auditoría
Toda aprobación o cancelación sobre comunicaciones SHALL generar evidencia auditable con actor, lote/comunicación afectada y resultado.

#### Scenario: Cancelación de lote queda auditada
- **WHEN** un aprobador cancela un lote de comunicaciones
- **THEN** el sistema registra un evento de auditoría atribuible al actor real con el identificador del lote
