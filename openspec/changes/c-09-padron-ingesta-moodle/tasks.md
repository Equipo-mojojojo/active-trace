## 1. Modelos y Migración

- [ ] 1.1 Crear `backend/app/models/padron.py` con modelos `VersionPadron` y `EntradaPadron` usando el mixin base del proyecto (tenant_id, timestamps, soft delete). `EntradaPadron.email` usa el helper de cifrado AES-256 de C-02.
- [ ] 1.2 Registrar los modelos en `backend/app/models/__init__.py` para que Alembic los detecte.
- [ ] 1.3 Generar Migración 006: tablas `version_padron` y `entrada_padron`. Índice parcial único en `(tenant_id, materia_id, cohorte_id)` WHERE `activa = true` en PostgreSQL.
- [ ] 1.4 Test: aislamiento multi-tenant en `VersionPadron` — una versión del tenant A no aparece en queries del tenant B.
- [ ] 1.5 Test: `EntradaPadron` con `usuario_id=NULL` se persiste sin error (alumno sin cuenta).
- [ ] 1.6 Test: email de `EntradaPadron` almacenado cifrado — el valor en DB no es texto plano.

## 2. Repository de Padrón (TDD: test primero)

- [ ] 2.1 Crear `backend/app/repositories/padron_repository.py` con métodos: `obtener_version_activa(materia_id, cohorte_id, tenant_id)`, `desactivar_version_activa(materia_id, cohorte_id, tenant_id, db)`, `crear_version(data, db)`, `crear_entradas_bulk(entradas, db)`, `listar_versiones(materia_id, cohorte_id, tenant_id)`, `soft_delete_version(version_id, db)`.
- [ ] 2.2 Test: `obtener_version_activa` retorna la única versión activa (o None si no existe).
- [ ] 2.3 Test: `desactivar_version_activa` pone `activa=false` sin borrar el registro.
- [ ] 2.4 Test: activar nueva versión en la misma (materia × cohorte) → versión anterior queda inactiva, nueva queda activa — todo en una transacción.
- [ ] 2.5 Test: `listar_versiones` retorna activa + históricas ordenadas por `cargado_at` DESC.

## 3. Parser de Archivos (TDD: test primero)

- [ ] 3.1 Crear `backend/app/services/padron_parser.py` con función `parse_padron(file_bytes: bytes, filename: str) -> list[dict]`. Soporta `.xlsx` (openpyxl) y `.csv` (stdlib). Detecta columnas insensible a mayúsculas/espacios.
- [ ] 3.2 Test: parse de csv básico con columnas nombre, apellidos, email, comision, regional.
- [ ] 3.3 Test: parse de xlsx con los mismos campos.
- [ ] 3.4 Test: headers en MAYÚSCULAS o con espacios son normalizados correctamente.
- [ ] 3.5 Test: archivo con más de 5000 filas lanza `PadronParseError` con mensaje de límite.
- [ ] 3.6 Test: extensión no soportada (`.pdf`) lanza `PadronParseError` con mensaje de formato.
- [ ] 3.7 Test: columna `grupo` es sinónimo de `comision` — ambas son detectadas.

## 4. Cliente Moodle WS (TDD: test primero)

- [ ] 4.1 Crear `backend/app/integrations/moodle_ws.py` con clase `MoodleWSClient` y métodos `get_enrolled_users(course_id)` y `get_course_activities(course_id)`. Exceptions: `MoodleWSError`, `MoodleNotConfiguredError`.
- [ ] 4.2 Test: `MoodleNotConfiguredError` cuando `MOODLE_URL` o `MOODLE_TOKEN` no están en env.
- [ ] 4.3 Test: `MoodleWSError` cuando el HTTP mock retorna error o timeout (usar `httpx` mock o `unittest.mock`).
- [ ] 4.4 Test: respuesta exitosa del LMS mockeada retorna lista de participantes con los campos esperados.

## 5. Service de Padrón (TDD: test primero)

- [ ] 5.1 Crear `backend/app/services/padron_service.py` con métodos: `preview(file_bytes, filename)`, `importar(actor, materia_id, cohorte_id, file_bytes, filename, db)`, `vaciar(actor, materia_id, cohorte_id, db)`, `listar_versiones(actor, materia_id, cohorte_id)`, `sync_moodle(actor, materia_id, cohorte_id, moodle_course_id, db)`, `sync_nocturna_all_tenants()`.
- [ ] 5.2 Test: `preview` retorna lista de alumnos parseados sin persistir nada en DB.
- [ ] 5.3 Test: `importar` crea nueva versión activa y desactiva la anterior en transacción única.
- [ ] 5.4 Test: `importar` registra auditoría `PADRON_CARGAR` con `actor_id` correcto.
- [ ] 5.5 Test: `vaciar` — PROFESOR puede vaciar su propia asignación, no la de otro.
- [ ] 5.6 Test: `vaciar` sin versión activa lanza `NotFound`.
- [ ] 5.7 Test: `sync_moodle` con LMS mockeado exitoso crea versión activa.
- [ ] 5.8 Test: `sync_moodle` con LMS mockeado fallido lanza `MoodleWSError` (el service lo propaga).
- [ ] 5.9 Test: `sync_nocturna_all_tenants` — fallo en tenant 2 no interrumpe tenant 3.

## 6. Schemas Pydantic

- [ ] 6.1 Crear `backend/app/schemas/padron.py` con `model_config = ConfigDict(extra='forbid')` en todos.
- [ ] 6.2 Schema `ImportarPadronRequest`: `materia_id: UUID`, `cohorte_id: UUID` (el archivo va como `UploadFile`).
- [ ] 6.3 Schema `EntradaPadronPreview`: `nombre`, `apellidos`, `email_enmascarado`, `comision`, `regional`.
- [ ] 6.4 Schema `PreviewResponse`: `alumnos: list[EntradaPadronPreview]`, `columnas_detectadas: list[str]`, `total: int`.
- [ ] 6.5 Schema `VersionPadronResponse`: `id`, `materia_id`, `cohorte_id`, `activa`, `cargado_at`, `total_entradas`.
- [ ] 6.6 Schema `SyncMoodleRequest`: `materia_id: UUID`, `cohorte_id: UUID`, `moodle_course_id: str`.

## 7. Router de Padrón

- [ ] 7.1 Crear `backend/app/api/v1/routers/padron.py` con prefix `/api/padron`.
- [ ] 7.2 `POST /preview` — sin persistencia; llama `PadronService.preview`; retorna `PreviewResponse`.
- [ ] 7.3 `POST /importar` — recibe `UploadFile` + form data; guard `require_permission("padron:importar")`; retorna 201.
- [ ] 7.4 `DELETE /vaciar` — guard `require_permission("padron:importar")`; llama `PadronService.vaciar`.
- [ ] 7.5 `GET /versiones` — guard `require_permission("padron:importar")`; llama `PadronService.listar_versiones`.
- [ ] 7.6 `POST /sync-moodle` — guard `require_permission("padron:importar")`; maneja `MoodleWSError` → 502, `MoodleNotConfiguredError` → 503.
- [ ] 7.7 Registrar el router en `backend/app/main.py`.
- [ ] 7.8 Verificar que el permiso `padron:importar` está en el seed de C-04; agregarlo si falta.

## 8. Tests de API (TDD: test primero)

- [ ] 8.1 Test: `POST /api/padron/preview` con xlsx válido → 200 con alumnos y columnas.
- [ ] 8.2 Test: `POST /api/padron/preview` con extensión inválida → 422.
- [ ] 8.3 Test: `POST /api/padron/importar` → 201, versión activa creada, auditoría registrada.
- [ ] 8.4 Test: `POST /api/padron/importar` sin permiso `padron:importar` → 403.
- [ ] 8.5 Test: `DELETE /api/padron/vaciar` — PROFESOR vacía su materia → 200, `activa=false`.
- [ ] 8.6 Test: `DELETE /api/padron/vaciar` — PROFESOR intenta vaciar materia ajena → 403.
- [ ] 8.7 Test: `GET /api/padron/versiones` → listado con activa + históricas.
- [ ] 8.8 Test: `POST /api/padron/sync-moodle` con LMS mockeado fallido → 502.
- [ ] 8.9 Test: `POST /api/padron/sync-moodle` con LMS no configurado → 503.
