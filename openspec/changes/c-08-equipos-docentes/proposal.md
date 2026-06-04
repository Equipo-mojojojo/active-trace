## Why

Con C-07 el modelo `Asignacion` quedó persistido y cubierto con CRUD base, pero no existe API de dominio orientada al flujo real de trabajo: un COORDINADOR no puede hoy configurar el equipo de un período nuevo sin hacerlo registro a registro, ni un docente puede ver el conjunto de sus materias activas. Este change entrega la capa de operaciones de equipo de alto valor que habilita el setup de cuatrimestre (FL-03) y desbloquea C-09, C-13, C-14 y C-16 en paralelo.

## What Changes

- Endpoint `GET /api/equipos/mis-equipos` — vista del docente sobre sus propias asignaciones (F4.2), con filtros y monitoreo de actividad.
- Endpoint `GET /api/equipos/asignaciones` — consulta de todas las asignaciones del tenant para COORDINADOR/ADMIN, con filtros multi-dimensionales (F4.3).
- Endpoint `POST /api/equipos/asignaciones/masiva` — alta de N docentes × materia × carrera × cohorte × rol + vigencia en un solo request (F4.4, RN-30).
- Endpoint `POST /api/equipos/clonar` — duplica todas las asignaciones vigentes de un equipo origen hacia un destino (materia × carrera × cohorte destino) con nuevas fechas de vigencia (F4.5, RN-12).
- Endpoint `PATCH /api/equipos/vigencia` — actualiza `desde`/`hasta` de todas las asignaciones de un equipo en bloque (F4.6).
- Endpoint `GET /api/equipos/export` — genera archivo descargable con el detalle del equipo (F4.7).
- Registro de auditoría `ASIGNACION_MODIFICAR` en todas las operaciones de escritura.
- Guard `equipos:asignar` en todos los endpoints de escritura (COORDINADOR, ADMIN); lectura propia sin guard extra.

## Capabilities

### New Capabilities

- `equipos-mis-equipos`: Vista personal de asignaciones activas/históricas del docente autenticado, con filtros y estado de vigencia derivado (F4.2).
- `equipos-gestion-coordinador`: Endpoints de consulta global y operaciones de escritura sobre asignaciones — masiva, clonar entre períodos, modificar vigencia en bloque y export (F4.3–F4.7).

### Modified Capabilities

_(ninguna — C-08 agrega API sobre el modelo `Asignacion` ya existente sin cambiar los requerimientos de ese spec)_

## Impact

- **Backend**: nuevos routers `backend/app/routers/equipos.py`, nuevo service `backend/app/services/equipos_service.py`. Sin cambios de modelo ni migración (usa `Asignacion` de C-07).
- **API surface**: 6 nuevos endpoints bajo `/api/equipos/*`.
- **Auditoría**: consume `AuditService` de C-05 para registrar `ASIGNACION_MODIFICAR`.
- **RBAC**: requiere permiso `equipos:asignar` ya seeded en C-04.
- **Dependencias de changes**: desbloquea trabajo en C-09 (padrón), C-13 (encuentros), C-14 (coloquios), C-16 (tareas) al completar la capa de equipos.
