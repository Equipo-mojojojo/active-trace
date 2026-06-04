## Context

El sistema no tiene todavía entidad de alumno importado. `Usuario` (E4) modela los usuarios del sistema (docentes, admin, etc.); los alumnos del LMS llegan como `EntradaPadron` — un registro desnormalizado por versión de padrón que puede existir sin cuenta de usuario. Este change crea esas entidades, la lógica de versionado, el parser de archivos y la integración con Moodle WS.

Restricción importante: `EntradaPadron.email` es PII y va **cifrada en reposo** (AES-256, igual que el resto de campos PII en el sistema). El helper `encrypt`/`decrypt` de C-02 ya existe en `app/core/security.py`.

## Goals / Non-Goals

**Goals:**
- Modelos `VersionPadron` + `EntradaPadron` con migración Alembic.
- API de importación (file upload + parse + preview + confirmar).
- API de vaciado con scope aislado por asignación (RN-04).
- Cliente `moodle_ws.py` con sync on-demand + nocturna.
- Audit `PADRON_CARGAR`.
- Cobertura ≥80% líneas, ≥90% reglas de negocio.

**Non-Goals:**
- No se importan calificaciones (eso es C-10).
- No se implementa la UI de importación (eso es C-22).
- La sync nocturna no requiere scheduler real en este change — el worker stub ya existe; basta con que el método sea invocable y testeado.

## Decisions

### D1 — Versionado: activar desactiva anterior (no hard delete)
**Por qué**: E6 del modelo de datos dice que al activar una nueva versión la anterior se desactiva pero no se borra. Esto preserva el historial y es consistente con soft delete transversal. La lógica: `UPDATE version_padron SET activa=false WHERE materia_id=X AND cohorte_id=Y AND activa=true` antes de `INSERT` la nueva versión.
**Nota sobre RN-05**: RN-05 dice "reemplaza completamente"; en términos de vista activa es correcto — solo hay una activa — pero los datos históricos no se destruyen. El comportamiento observable para el usuario es el mismo (el padrón activo cambia), con la ventaja de poder auditar versiones anteriores.

### D2 — Parser separado: `padron_parser.py`
**Por qué**: la lógica de detectar columnas en xlsx/csv es independiente de la persistencia. Separar el parser en `services/padron_parser.py` lo hace testeable sin tocar la DB, con entradas/salidas puras (bytes → list[dict]). El service orquesta: recibe bytes → llama parser → valida → persiste.
**Formatos soportados**: `.xlsx` (openpyxl) y `.csv` (stdlib csv). Si la extensión no es ninguna de las dos → 422.
**Columnas detectadas**: `nombre`, `apellido` (o `apellidos`), `email`, `comision` (o `grupo`), `regional`. Insensible a mayúsculas y espacios en el header.

### D3 — Preview sin persistencia
**Por qué**: el flujo de F1.3 muestra una vista previa antes de confirmar la carga. El endpoint `POST /api/padron/preview` recibe el archivo, lo parsea en memoria y retorna el resultado sin tocar la DB. El frontend muestra los datos; el usuario confirma con `POST /api/padron/importar` (que también recibe el archivo — sin sesión de upload intermedia, para simplicidad).

### D4 — Moodle WS: cliente desacoplado con fallback
**Por qué**: `integrations/moodle_ws.py` encapsula la comunicación con Moodle. El service llama al cliente; si el cliente lanza `MoodleWSError` (timeout o respuesta no 2xx), el service captura y retorna 502 al caller con mensaje de reintento. El fallback manual (import desde archivo) es la misma ruta que D2.
**Credenciales**: `MOODLE_URL` y `MOODLE_TOKEN` son variables de entorno opcionales. Si no están configuradas, el endpoint de sync retorna 503 con mensaje claro.

### D5 — Vaciado scope-isolated (RN-04)
**Por qué**: RN-04 dice que vaciar afecta solo `(usuario_que_vacía × materia)`. Implementación: soft delete sobre `VersionPadron` de la asignación del actor (no de toda la materia). COORDINADOR puede vaciar cualquier versión del tenant. Un PROFESOR solo puede vaciar su propia versión activa.

### D6 — Email de EntradaPadron cifrado en reposo
**Por qué**: regla dura del proyecto. Se usa el mismo helper AES-256 de C-02. El email no aparece en logs ni en respuestas de API en texto plano; se retorna solo cuando el actor tiene permiso explícito (por ahora no se expone en ningún endpoint de listado).

## Risks / Trade-offs

- [Riesgo] `openpyxl` puede ser pesado para archivos muy grandes → Mitigación: límite de 5000 filas en el parser; rechaza con 422 si se supera.
- [Trade-off] Preview recibe el archivo dos veces (preview + confirm) → aceptado para MVP; evita la complejidad de sesiones de upload temporales.
- [Riesgo] Moodle WS puede tener latencia alta en sync on-demand → Mitigación: timeout de 30s configurable; si excede → 502.

## Migration Plan

Migración 006 (sin rollback de datos — nueva tabla):
1. Crear `version_padron` y `entrada_padron`.
2. Índice único en `(tenant_id, materia_id, cohorte_id, activa)` donde `activa=true` (índice parcial en PG).
3. No hay datos previos que migrar.
