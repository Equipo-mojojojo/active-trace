## ADDED Requirements

### Requirement: Lista de comisiones del profesor
El sistema SHALL mostrar al PROFESOR una grilla de cards con todas sus comisiones del período activo. Cada card muestra nombre de materia, cohorte, cantidad de alumnos y un badge de estado ("Importado" en verde si tiene calificaciones cargadas, "Sin datos" en gris si no).

#### Scenario: Profesor con comisiones cargadas
- **WHEN** el PROFESOR navega a `/profesor/comisiones`
- **THEN** el sistema muestra una grilla de cards, una por comisión asignada, con nombre de materia, cohorte, cantidad de alumnos y badge de estado

#### Scenario: Profesor sin comisiones
- **WHEN** el PROFESOR navega a `/profesor/comisiones` y no tiene comisiones asignadas
- **THEN** el sistema muestra un estado vacío con mensaje informativo

#### Scenario: Acceso denegado sin permiso
- **WHEN** un usuario sin permiso `atrasados:ver` navega a `/profesor/comisiones`
- **THEN** el PermissionGuard redirige a `/403`

---

### Requirement: Importación de calificaciones con stepper
El sistema SHALL guiar al PROFESOR a través de un flujo de 3 pasos para importar calificaciones: (1) subir archivo, (2) seleccionar actividades, (3) confirmar. El paso 2 muestra una tabla de preview con las actividades detectadas en el archivo, permitiendo incluir/excluir cada una mediante checkbox.

#### Scenario: Upload exitoso y preview de actividades
- **WHEN** el PROFESOR sube un archivo CSV/XLSX válido en el paso 1
- **THEN** el sistema avanza al paso 2 y muestra la tabla de actividades detectadas con nombre, tipo (Numérica/Texto) y ejemplos de valores

#### Scenario: Confirmación con actividades seleccionadas
- **WHEN** el PROFESOR selecciona al menos una actividad y confirma en el paso 3
- **THEN** el sistema llama al endpoint de confirmación y redirige a la vista de comisión con los datos calculados

#### Scenario: Archivo inválido
- **WHEN** el PROFESOR sube un archivo con formato no soportado o sin actividades detectables
- **THEN** el sistema muestra un mensaje de error descriptivo sin avanzar de paso

#### Scenario: Acceso denegado sin permiso de importar
- **WHEN** un usuario sin permiso `calificaciones:importar` navega al flujo de importación
- **THEN** el PermissionGuard redirige a `/403`

---

### Requirement: Configuración de umbral de aprobación
El sistema SHALL permitir al PROFESOR configurar el porcentaje mínimo que define si un alumno está "al día" o "atrasado" en su comisión. El valor por defecto es 60%. El umbral se aplica a todos los cálculos de esa comisión.

#### Scenario: Cambio de umbral
- **WHEN** el PROFESOR modifica el valor del umbral y lo guarda
- **THEN** el sistema persiste el nuevo umbral y recalcula la vista de atrasados con el nuevo valor

#### Scenario: Umbral por defecto al crear comisión
- **WHEN** el PROFESOR accede a una comisión sin umbral configurado
- **THEN** el sistema muestra el valor 60% como valor por defecto

---

### Requirement: Vista de atrasados con tabs de análisis
El sistema SHALL mostrar en la comisión del PROFESOR una navegación por tabs: "Atrasados", "Ranking", "Notas Finales", "Entregas sin corregir". El tab activo por defecto es "Atrasados".

#### Scenario: Tab Atrasados — tabla de alumnos atrasados
- **WHEN** el PROFESOR está en el tab "Atrasados"
- **THEN** el sistema muestra una tabla con columnas Alumno, Legajo, Actividades faltantes, Nota promedio, Estado (badge rojo "Atrasado") y paginación

#### Scenario: Tab Ranking — ordenado por actividades aprobadas
- **WHEN** el PROFESOR navega al tab "Ranking"
- **THEN** el sistema muestra la tabla de alumnos ordenada de mayor a menor por cantidad de actividades aprobadas

#### Scenario: Tab Notas Finales — calificaciones agrupadas
- **WHEN** el PROFESOR navega al tab "Notas Finales"
- **THEN** el sistema muestra la nota final calculada por alumno, lista para exportar

#### Scenario: Tab Entregas sin corregir
- **WHEN** el PROFESOR navega al tab "Entregas sin corregir"
- **THEN** el sistema muestra la lista de entregas detectadas como pendientes de corrección y un botón de export a CSV

#### Scenario: Sin datos importados
- **WHEN** el PROFESOR accede a cualquier tab sin haber importado calificaciones
- **THEN** el sistema muestra un estado vacío con CTA para ir al flujo de importación
