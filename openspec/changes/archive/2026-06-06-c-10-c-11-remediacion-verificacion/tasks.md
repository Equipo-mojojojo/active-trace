## 1. Readiness del entorno y prerequisitos de validación

- [x] 1.1 Verificar la declaración de dependencias de parseo en `backend/pyproject.toml` y ajustar el flujo de instalación local para que `pandas` y `openpyxl` queden efectivamente disponibles en el entorno backend.
- [x] 1.2 Documentar el prerequisito de `TEST_DATABASE_URL` y los comandos de validación dirigidos para C-10/C-11 en la documentación operativa adecuada del backend.
- [x] 1.3 Agregar un chequeo automatizable o instrucción verificable que confirme que las dependencias de parseo pueden importarse sin `ModuleNotFoundError` antes de correr la suite objetivo.

## 2. Corrección de resolución de padrón en C-10 (TDD primero)

- [x] 2.1 Escribir o ajustar tests que expongan el bug actual de resolución de `EntradaPadron` en `calificaciones_service.py` cuando el servicio intenta usar un campo académico inexistente.
- [x] 2.2 Diseñar la estrategia de lookup del padrón válido para C-10 usando `VersionPadron` → `EntradaPadron`, definiendo cómo se selecciona la versión correcta dentro del contexto de materia/asignación/cohorte.
- [x] 2.3 Implementar en repositories/services de C-10 la resolución correcta de alumnos contra el padrón versionado válido, eliminando cualquier dependencia de `EntradaPadron.materia_id`.
- [x] 2.4 Ajustar preview/import/finalización de C-10 para que usen el mismo criterio de resolución de padrón y fallen con error claro si no existe un padrón válido para cruzar alumnos.
- [x] 2.5 Revisar si el contrato de request/schema de C-10 necesita endurecer contexto académico (por ejemplo asignación/cohorte) y aplicar el cambio mínimo necesario sin romper el alcance del change.

## 3. Alineación ORM y filtros de C-11 (TDD primero)

- [x] 3.1 Escribir o ajustar tests que demuestren que el monitor debe filtrar por email en `q` y por `importado_at` para rango de fechas.
- [x] 3.2 Mapear `importado_at` en `backend/app/models/calificacion.py` y alinear cualquier query/repository que dependa de ese timestamp persistido.
- [x] 3.3 Corregir `analisis_repository.py` y `analisis_service.py` para que obtengan entradas/calificaciones sin asumir `EntradaPadron.materia_id` y respeten el modelo versionado real.
- [x] 3.4 Ajustar el filtro `q` del monitor para que contemple nombre, apellidos y email del alumno dentro del scope permitido por JWT.
- [x] 3.5 Validar que `fecha_desde`/`fecha_hasta` solo apliquen a COORDINADOR/ADMIN usando `importado_at` como fuente de verdad.

## 4. Remediación de tests de C-10 y C-11

- [x] 4.1 Actualizar los tests unitarios de parser/import/finalización para que cubran la resolución correcta de padrón versionado y no oculten errores estructurales del modelo.
- [x] 4.2 Actualizar los tests de monitor/análisis para cubrir búsqueda por email, filtros de fecha y el uso correcto del timestamp de importación.
- [x] 4.3 Ejecutar y corregir la suite unitaria objetivo de `test_calificaciones_c10.py` y `test_analisis_c11.py` hasta que deje de fallar por inconsistencias funcionales.
- [x] 4.4 Ejecutar con `TEST_DATABASE_URL` los tests de integración/E2E relevantes para C-10/C-11 y corregir cualquier drift adicional detectado dentro del alcance del change.

## 5. Validación final y evidencia del change

- [x] 5.1 Ejecutar una corrida final de validación para C-10/C-11 incluyendo dependencias instaladas y tests dirigidos relevantes, registrando resultados.
- [x] 5.2 Confirmar que no queden referencias runtime a campos ORM inexistentes ni filtros del monitor fuera de contrato.
- [x] 5.3 Preparar el change para `/opsx:apply` dejando proposal, design, specs y tasks alineados con los hallazgos de auditoría y la estrategia de remediación.
