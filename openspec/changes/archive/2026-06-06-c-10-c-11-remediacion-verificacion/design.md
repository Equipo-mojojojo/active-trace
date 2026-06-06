## Context

C-10 (`calificaciones-y-umbral`) y C-11 (`analisis-atrasados-reportes`) quedaron funcionalmente avanzados, pero la auditoría encontró una desalineación importante entre dominio, migraciones, ORM y verificación. El modelo de padrón versionado ubica `materia_id` y `cohorte_id` en `VersionPadron`, no en `EntradaPadron`; sin embargo, parte del código de calificaciones y análisis intenta leer `EntradaPadron.materia_id`, lo que rompe el contrato real del modelo. En paralelo, la migración de `Calificacion` ya define `importado_at`, pero el modelo ORM no lo expone, debilitando los filtros por fecha del monitor. Finalmente, el entorno local no estaba ejecutando la validación prometida porque faltaban dependencias de parseo (`pandas`, `openpyxl`) y la suite con DB real no tenía precondiciones explícitas.

El objetivo del cambio es corregir la implementación para que respete el dominio ya definido, fortalecer el contrato de filtrado/seguimiento y cerrar la brecha de verificación antes de avanzar con features dependientes como C-12.

## Goals / Non-Goals

**Goals:**
- Reencauzar C-10/C-11 para que resuelvan alumnos y calificaciones sobre el padrón versionado real (`VersionPadron` → `EntradaPadron`).
- Alinear el modelo ORM de `Calificacion` con la migración vigente, incluyendo `importado_at` para consultas del monitor.
- Garantizar que el monitor cumpla el contrato OpenSpec de búsqueda por nombre/email y rango de fechas.
- Asegurar que el entorno backend tenga disponibles las dependencias de parseo requeridas por los flujos `.csv/.xlsx` y por sus tests.
- Ejecutar una validación reproducible (unitaria + integración/E2E relevantes) y dejar evidencia suficiente para aplicar el change con confianza.

**Non-Goals:**
- No rediseñar la UX o los endpoints de C-10/C-11 más allá de lo necesario para cerrar inconsistencias funcionales.
- No alterar reglas de negocio de aprobación, ranking o atrasados fuera de los defectos detectados.
- No introducir nuevas capacidades de reporting distintas a las ya previstas por C-10/C-11.
- No adelantar trabajo de C-12 ni de módulos posteriores.

## Decisions

### 1. Resolver el padrón a través de `VersionPadron`, no duplicando `materia_id` en `EntradaPadron`
- **Decision:** las consultas de C-10/C-11 deben obtener `EntradaPadron` por join o lookup a su `VersionPadron` activa, respetando el diseño versionado existente.
- **Why:** el dominio y la migración ya ubican la identidad académica del padrón en la versión, no en cada entrada. Agregar ahora `materia_id` a `EntradaPadron` duplicaría datos, abriría riesgo de inconsistencia y rompería el diseño archivado de C-09.
- **Alternatives considered:**
  - **Agregar `materia_id` a `EntradaPadron`**: descartado por duplicación de estado y necesidad de nueva migración sin beneficio claro.
  - **Mantener queries actuales y parchear tests**: descartado porque deja errores runtime latentes.

### 2. Alinear `Calificacion` ORM con `importado_at` persistido
- **Decision:** mapear explícitamente `importado_at` en el modelo ORM y usarlo como fuente de verdad para filtros de fecha en monitor/reportes.
- **Why:** el esquema ya lo persiste y OpenSpec lo usa semánticamente en F2.9. Sin el campo en ORM, el filtro existe solo de manera parcial y no verificable.
- **Alternatives considered:**
  - **Filtrar por `created_at`**: descartado porque cambia semántica y contradice el dato ya modelado en migración.
  - **Eliminar filtro por fecha del monitor**: descartado porque reduciría comportamiento ya especificado.

### 3. Corregir el monitor según contrato de búsqueda libre
- **Decision:** el parámetro `q` debe buscar por nombre, apellidos y email del alumno dentro del scope permitido por JWT.
- **Why:** OpenSpec y KB ya prometen búsqueda libre por alumno/correo; la implementación actual solo cubre nombre/apellido.
- **Alternatives considered:**
  - **Limitar el spec a nombre/apellido**: descartado porque sería degradar una capacidad ya declarada.

### 4. Tratar dependencias de parseo y DB de test como parte del readiness del change
- **Decision:** el change incluirá una capa explícita de readiness/verificación: dependencias Python instaladas, precondiciones de `TEST_DATABASE_URL`, y comandos de validación documentados y ejecutados.
- **Why:** en la práctica, hoy gran parte del “drift” es invisible si el entorno no permite correr las pruebas relevantes.
- **Alternatives considered:**
  - **Dejar la instalación a criterio manual fuera del change**: descartado porque impide cerrar el cambio con evidencia reproducible.

## Risks / Trade-offs

- **[Riesgo]** La resolución correcta de padrón para C-10 podría requerir usar contexto de asignación/cohorte donde hoy algunos caminos solo reciben `materia_id`.  
  **Mitigation:** diseñar primero la estrategia de lookup sobre la versión activa y, si hace falta, endurecer validaciones o payloads antes de escribir código.

- **[Riesgo]** Los tests con DB real pueden revelar más drift histórico que el detectado en la auditoría rápida.  
  **Mitigation:** ejecutar primero unit tests y luego integración/E2E con `TEST_DATABASE_URL`, registrando cualquier gap adicional como parte del mismo change si aún está en alcance.

- **[Riesgo]** Instalar dependencias faltantes puede exponer diferencias entre entorno local y lo declarado en `pyproject.toml`.  
  **Mitigation:** validar instalación desde el lock/declaración actual y actualizar documentación/configuración del entorno si hay pasos faltantes.

- **[Trade-off]** Elegir joins/versionado explícito en vez de campos redundantes puede requerir más cambios en repositories/services.  
  **Mitigation:** mantener la corrección de dominio como prioridad para no introducir deuda estructural nueva.
