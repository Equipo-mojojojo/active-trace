## Why

Con C-07 el modelo `Usuario` y `Asignacion` están listos, pero no existe todavía ninguna entidad de alumno importado ni conexión con Moodle. Sin el padrón no hay datos sobre quiénes cursan cada materia — y sin eso, C-10 (calificaciones), C-11 (atrasados) y C-12 (comunicaciones) no tienen sobre qué operar. Este change cierra la brecha entre el LMS y activia-trace al nivel más básico: saber quiénes son los alumnos de cada comisión.

## What Changes

- Nuevos modelos `VersionPadron` y `EntradaPadron` con Migración 006: una versión activa por (materia × cohorte) en simultáneo; activar una nueva desactiva la anterior sin borrarla.
- `POST /api/padron/importar` — carga un archivo `.xlsx`/`.csv`, genera vista previa de alumnos detectados y, una vez confirmada, crea la nueva versión activa del padrón (F1.3, F1.4). Requiere permiso `padron:importar`.
- `GET /api/padron/preview` — retorna el parseo del archivo subido sin persistirlo: alumnos, comisiones y columnas detectadas.
- `DELETE /api/padron/vaciar` — elimina la versión activa del padrón de una materia×cohorte (F1.5, RN-04). PROFESOR solo puede vaciar su propio scope; COORDINADOR vacía cualquiera del tenant.
- `GET /api/padron/versiones` — historial de versiones (activa + anteriores) de una materia×cohorte.
- Cliente de integración `integrations/moodle_ws.py`: consume Moodle Web Services para sincronizar participantes y actividades. Sync on-demand (`POST /api/padron/sync-moodle`) y nocturna via worker. Errores del LMS mapean a `502` con reintento.
- Audit `PADRON_CARGAR` en cada importación exitosa.

## Capabilities

### New Capabilities

- `padron-versionado`: Modelos `VersionPadron` + `EntradaPadron`, lógica de activación/desactivación de versiones, migración y API de historial. Email de alumno `[cifrado]`.
- `padron-importacion-archivo`: Endpoint de importación con parse de xlsx/csv, detección de columnas (nombre, apellido, email, comisión, regional), vista previa y confirmación de carga (F1.3, F1.4, F1.5).
- `moodle-ws-integracion`: Cliente `moodle_ws.py`, sync on-demand y nocturna de participantes, manejo de errores 502 con reintento configurable.

### Modified Capabilities

_(ninguna — C-09 introduce entidades y flujos nuevos sin alterar specs existentes)_

## Impact

- **Modelos**: `backend/app/models/padron.py` — `VersionPadron`, `EntradaPadron` (PII cifrada).
- **Migración**: `Migración 006: version_padron, entrada_padron`.
- **Backend**: repositories/padron_repository.py, services/padron_service.py, services/padron_parser.py (parse xlsx/csv), integrations/moodle_ws.py, routers/padron.py.
- **Dependencias de changes**: desbloquea C-10 (calificaciones) que depende de `EntradaPadron`.
- **Libs nuevas**: `openpyxl` (parse xlsx), `python-multipart` (file upload) — verificar si ya están en pyproject.toml.
