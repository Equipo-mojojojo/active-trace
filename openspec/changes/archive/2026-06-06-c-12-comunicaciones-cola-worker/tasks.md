## 1. Modelo y persistencia de comunicaciones

- [x] 1.1 Crear la migración y el modelo `Comunicacion` con `tenant_id`, `lote_id`, destinatario cifrado, payload renderizado y estados del ciclo de vida.
- [x] 1.2 Implementar repository tenant-scoped para crear, consultar y transicionar comunicaciones de forma segura e idempotente.
- [x] 1.3 Definir enums, schemas y validaciones de dominio para estados válidos, cancelación y tracking por lote/destinatario.

## 2. Preview y encolado

- [x] 2.1 Implementar el servicio de preview que resuelve destinatarios dentro del scope del actor y renderiza asunto/cuerpo sin persistir comunicaciones.
- [x] 2.2 Implementar el servicio de confirmación de envío que crea una `Comunicacion` por destinatario agrupada por `lote_id`.
- [x] 2.3 Exponer endpoints protegidos para preview, encolado y consulta de estado con `comunicacion:enviar`.

## 3. Aprobación y cancelación

- [x] 3.1 Modelar la regla configurable por tenant que determina si un lote necesita aprobación previa antes del despacho.
- [x] 3.2 Implementar operaciones de aprobar/cancelar por lote y por comunicación individual con guard `comunicacion:aprobar`.
- [x] 3.3 Registrar auditoría de envíos, aprobaciones y cancelaciones con evidencia por actor y lote/comunicación afectada.

## 4. Worker asíncrono de despacho

- [x] 4.1 Implementar el worker que toma únicamente comunicaciones elegibles y las pasa por `Pendiente -> Enviando -> Enviado/Error`.
- [x] 4.2 Encapsular el canal de despacho detrás de un adapter o servicio para permitir retry/control de errores sin acoplar la API HTTP.
- [x] 4.3 Integrar el worker con el entrypoint existente de `workers/` y asegurar que los mensajes cancelados o no aprobados no se procesen.

## 5. Validación y cobertura

- [x] 5.1 Agregar tests de máquina de estados, cifrado del destinatario y reglas de transición válidas/inválidas.
- [x] 5.2 Agregar tests de preview, aprobación/cancelación por lote e individual, y aislamiento tenant/scope del actor.
- [x] 5.3 Agregar tests del worker para procesamiento exitoso, error de despacho y exclusión de mensajes no aprobados.
