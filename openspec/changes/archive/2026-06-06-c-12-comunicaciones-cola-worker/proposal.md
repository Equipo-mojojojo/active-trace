## Why

El flujo central del profesor ya puede importar, analizar y detectar alumnos atrasados, pero todavía no puede cerrar el circuito con comunicaciones trazables a los alumnos. C-12 habilita el tramo final del camino crítico con preview obligatorio, aprobación configurable y despacho asíncrono auditable para evitar envíos erróneos o bloqueantes.

## What Changes

- Incorporar el modelo `Comunicacion` con destinatario cifrado, lote, estados controlados y trazabilidad por tenant.
- Exponer endpoints para preview, encolado, consulta de estado, aprobación/cancelación por lote o por destinatario y tracking del resultado.
- Agregar un worker asíncrono de despacho que procese la cola respetando aprobación previa configurable por tenant.
- Registrar auditoría de envíos y decisiones de aprobación/cancelación sobre comunicaciones masivas.

## Capabilities

### New Capabilities
- `comunicacion-modelo`: contrato del modelo de comunicación, estados y cifrado de destinatarios.
- `comunicacion-preview`: preview obligatoria antes de encolar comunicaciones a alumnos.
- `comunicacion-cola-worker`: procesamiento asíncrono de la cola de comunicaciones y tracking de estados.
- `comunicacion-aprobacion`: aprobación humana configurable por tenant para envíos masivos.

### Modified Capabilities

## Impact

- Backend: modelos, schemas, repositories, services, routers y worker de comunicaciones.
- Base de datos: nueva migración para `comunicacion`.
- Seguridad y operaciones: permisos `comunicacion:enviar` / `comunicacion:aprobar`, cifrado en reposo y auditoría.
- OpenSpec: nuevas specs para preview, cola/worker, aprobación y modelo de comunicación.
