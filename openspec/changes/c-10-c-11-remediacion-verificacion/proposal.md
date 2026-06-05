## Why

La auditoría de C-10 y C-11 mostró drift entre los specs, las migraciones y la implementación real: hoy hay consultas que dependen de campos ORM inexistentes, filtros del monitor que no cubren todo lo prometido por OpenSpec y una verificación automatizada incompleta por dependencias faltantes y tests de integración sin ejecutar. Necesitamos cerrar esa brecha ahora para que el flujo de calificaciones y análisis quede confiable antes de avanzar con cambios dependientes como C-12.

## What Changes

- Corregir la resolución de `EntradaPadron` en C-10/C-11 para que use el modelo/versionado real del padrón en vez de asumir columnas inexistentes.
- Alinear el modelo ORM de `Calificacion` con la migración vigente, incluyendo el timestamp de importación usado por filtros del monitor.
- Ajustar el monitor de seguimiento para que cumpla el contrato de búsqueda y filtrado prometido por OpenSpec.
- Completar la instalación/configuración de dependencias necesarias para parseo de archivos LMS y padrón (`pandas`, `openpyxl`) dentro del entorno de trabajo y del flujo de verificación.
- Ejecutar y dejar documentada una validación de tests unitaria, de integración y E2E para C-10/C-11 con precondiciones explícitas (`TEST_DATABASE_URL`, dependencias Python instaladas).

## Capabilities

### New Capabilities
- `c10-c11-verification-readiness`: define el contrato operativo mínimo para ejecutar las validaciones automatizadas de calificaciones y análisis (dependencias Python instaladas, base de test disponible y evidencia de corrida exitosa).

### Modified Capabilities
- `calificaciones-import`: aclarar que el import y la preview resuelven alumnos contra el padrón versionado activo real de la materia/cohorte, sin depender de columnas inexistentes en `EntradaPadron`.
- `finalizacion-import`: aclarar que la detección de pendientes usa el padrón versionado activo y cruza correctamente las calificaciones textuales persistidas antes de marcar trabajos sin corregir.
- `monitor-seguimiento`: ajustar el contrato de búsqueda libre y filtros de fecha para que contemplen email del alumno y el timestamp persistido de importación de calificaciones.

## Impact

- Código backend afectado en modelos ORM, repositories y services de `calificaciones`, `analisis` y su integración con `padron`.
- Posibles ajustes en schemas/respuestas del monitor y en consultas tenant-scoped.
- Dependencias y entorno del backend (`pyproject.toml`, instalación local, documentación de test setup).
- Suite de tests de `backend/tests/test_calificaciones_c10.py` y `backend/tests/test_analisis_c11.py`, más validaciones relacionadas de padrón/monitor.
