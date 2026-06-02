## ADDED Requirements

### Requirement: El sistema SHALL almacenar registros de auditoría en una tabla append-only

El sistema SHALL persistir los registros de auditoría en una tabla `audit_log` con los siguientes campos:
- `id`: UUID primary key
- `tenant_id`: UUID, FK → Tenant, NOT NULL
- `fecha_hora`: DateTime with timezone, NOT NULL, server default `now()`
- `actor_id`: UUID, FK → Usuario, NOT NULL — usuario real que ejecutó la acción
- `impersonado_id`: UUID, FK → Usuario, NULL — usuario impersonado (solo si la acción se ejecutó bajo impersonación)
- `materia_id`: UUID, FK → Materia, NULL — materia asociada a la acción (opcional)
- `accion`: String(100), NOT NULL — código estandarizado de la acción (ej: `CALIFICACIONES_IMPORTAR`)
- `detalle`: JSONB, NULL — contexto adicional de la acción
- `filas_afectadas`: Integer, NULL — cantidad de registros afectados por la acción
- `ip`: String(45), NULL — dirección IP del cliente
- `user_agent`: String(500), NULL — User-Agent del cliente
- `created_at`: DateTime with timezone, NOT NULL, server default `now()`

#### Scenario: Crear un registro de auditoría
- **WHEN** se ejecuta una acción significativa
- **THEN** el sistema SHALL crear un registro en `audit_log` con actor_id, accion, tenant_id y fecha_hora
- **THEN** el sistema SHALL registrar ip y user_agent capturados por el middleware

### Requirement: La tabla audit_log SHALL ser append-only (sin UPDATE ni DELETE)

El sistema SHALL garantizar que ningún registro de auditoría pueda ser modificado o eliminado, ni por la aplicación ni por acceso directo a la base de datos.

#### Scenario: Rechazar UPDATE sobre audit_log
- **WHEN** se ejecuta una sentencia UPDATE sobre la tabla `audit_log`
- **THEN** la base de datos SHALL rechazar la operación con un error

#### Scenario: Rechazar DELETE sobre audit_log
- **WHEN** se ejecuta una sentencia DELETE sobre la tabla `audit_log`
- **THEN** la base de datos SHALL rechazar la operación con un error

#### Scenario: El service layer nunca expone update/delete
- **WHEN** se escribe el AuditService
- **THEN** NO SHALL tener métodos de actualización ni eliminación de registros

### Requirement: El sistema SHALL incluir un catálogo de códigos de acción

El sistema SHALL definir un conjunto fijo de códigos de acción como constantes en Python. El catálogo inicial incluye:

- `CALIFICACIONES_IMPORTAR` — Importación de calificaciones desde archivo externo
- `PADRON_CARGAR` — Carga de nueva versión del padrón
- `COMUNICACION_ENVIAR` — Envío de comunicación a alumnos
- `ASIGNACION_MODIFICAR` — Modificación de un equipo docente
- `LIQUIDACION_CERRAR` — Cierre de una liquidación mensual
- `IMPERSONACION_INICIAR` — Inicio de sesión de impersonación
- `IMPERSONACION_FINALIZAR` — Fin de sesión de impersonación

#### Scenario: Registrar acción con código válido
- **WHEN** el AuditService registra una acción con un código del catálogo
- **THEN** el registro se guarda correctamente

#### Scenario: Rechazar código de acción inválido
- **WHEN** el AuditService recibe un código que no está en el catálogo
- **THEN** el sistema SHALL rechazar el registro con error de validación
