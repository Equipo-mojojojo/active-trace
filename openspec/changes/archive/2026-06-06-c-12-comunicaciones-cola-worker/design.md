## Context

Después de C-11 el sistema ya identifica alumnos atrasados y entregas sin corregir, pero el paso siguiente del flujo docente sigue fuera de la plataforma: no existe un mecanismo trazable para generar, aprobar y despachar comunicaciones a alumnos. C-12 agrega un modelo persistente de comunicaciones, endpoints protegidos por permisos finos y un worker asíncrono que procesa la cola sin bloquear las requests HTTP.

La solución debe respetar constraints ya vigentes del proyecto: tenant scoping por defecto, identidad derivada solo del JWT, destinatarios cifrados en reposo, auditoría de acciones significativas y separación Clean Architecture entre routers, services y repositories.

## Goals / Non-Goals

**Goals:**
- Modelar comunicaciones masivas con estados explícitos y transición controlada.
- Exigir preview antes de encolar mensajes a alumnos.
- Soportar aprobación humana configurable por tenant antes del despacho.
- Ejecutar el envío en un worker asíncrono desacoplado de la API.
- Exponer tracking de estado y operaciones de cancelación/aprobación sin romper aislamiento multi-tenant.

**Non-Goals:**
- Implementar mensajería interna entre usuarios del sistema.
- Resolver definitivamente el canal externo de entrega (SMTP/N8N/etc.) más allá del contrato del worker.
- Diseñar frontend de comunicaciones; este change cubre backend y contratos.

## Decisions

### 1. Persistir una fila por destinatario, agrupable por `lote_id`
Cada destinatario tendrá su propia entidad `Comunicacion` y los envíos masivos se agrupan por `lote_id`. Esto simplifica tracking, aprobación parcial, cancelación individual y auditoría fina.

**Alternativas consideradas:**
- Un registro por lote con payload embebido de destinatarios. Rechazada porque complica transiciones y reintentos por destinatario.

### 2. Mantener máquina de estados explícita en dominio
El service controlará transiciones `Pendiente -> Enviando -> Enviado/Error` y `Pendiente -> Cancelado`, más la variante de aprobación previa antes de que el worker tome el mensaje. Esto permite testear reglas de negocio sin depender del canal real.

**Alternativas consideradas:**
- Delegar estados implícitamente al worker. Rechazada porque vuelve opaca la lógica y dificulta validaciones previas.

### 3. Exigir preview antes de crear comunicaciones persistidas
La preview genera asunto/cuerpo resuelto contra destinatarios seleccionados pero no crea filas definitivas. El encolado reutiliza la misma composición con plantillas y variables conocidas del dominio.

**Alternativas consideradas:**
- Permitir envío directo sin preview. Rechazada por RN-16 y por el riesgo operativo de envíos erróneos.

### 4. Usar aprobación configurable por tenant como gate lógico previo al worker
Si el tenant requiere aprobación, las comunicaciones quedan retenidas hasta acción explícita de un actor con `comunicacion:aprobar`. Si no la requiere, el worker puede procesar directamente los mensajes pendientes.

**Alternativas consideradas:**
- Un flujo global obligatorio para todos los tenants. Rechazada porque el dominio exige configuración por tenant.

## Risks / Trade-offs

- **Canal externo no definido en detalle** → Mitigar encapsulando el despacho detrás de un servicio/adapter del worker.
- **Errores de concurrencia en el worker** → Mitigar con transiciones idempotentes y selección de mensajes solo en estados válidos.
- **Exposición accidental de PII en logs** → Mitigar cifrando destinatarios en reposo y logueando solo IDs/lotes/contadores.
- **Aprobación parcial añade complejidad de UX y dominio** → Mitigar modelando operaciones por lote y por comunicación individual desde el inicio.

## Migration Plan

1. Crear migración `comunicacion` con `tenant_id`, `lote_id`, estado, payload renderizado y destinatario cifrado.
2. Agregar permisos/guards necesarios para enviar y aprobar comunicaciones.
3. Implementar repositorio, service y routers para preview, encolado, aprobación, cancelación y consulta.
4. Integrar worker asíncrono para tomar pendientes válidos y actualizar estados.
5. Cubrir con tests de máquina de estados, cifrado, aprobación, cancelación y procesamiento del worker.

## Open Questions

- Qué adapter concreto usará el worker para el despacho inicial (stub interno, SMTP o integración externa) durante la primera implementación.
- Dónde vivirá la configuración por tenant de “requiere aprobación” si hoy aún no existe una tabla/config dedicada para esa preferencia.
