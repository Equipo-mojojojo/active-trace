## ADDED Requirements

### Requirement: El backend declara y tiene disponibles las dependencias de parseo requeridas por C-10/C-11
El backend SHALL poder ejecutar los flujos de importación y preview de C-10/C-11 con las dependencias Python declaradas para parseo tabular (`pandas`) y archivos Excel (`openpyxl`) instaladas en el entorno activo donde se valida el change.

#### Scenario: El entorno puede importar las dependencias declaradas
- **WHEN** se ejecuta la validación técnica del change en el entorno backend
- **THEN** `pandas` y `openpyxl` están instalados y pueden importarse sin `ModuleNotFoundError`

#### Scenario: Los tests de parseo dejan de fallar por dependencias faltantes
- **WHEN** se ejecutan los tests unitarios de C-10/C-11 que parsean `.csv` y `.xlsx`
- **THEN** no fallan por ausencia de librerías requeridas por el parser

### Requirement: La verificación del change exige prerequisitos explícitos para tests con DB real
La validación de C-10/C-11 SHALL documentar y usar precondiciones explícitas para los tests que requieren base real, incluyendo `TEST_DATABASE_URL` y una corrida dirigida de suites unitarias/integración/E2E relevantes.

#### Scenario: Los tests con DB real tienen prerequisito visible
- **WHEN** un desarrollador prepara la validación de C-10/C-11
- **THEN** sabe que debe proveer `TEST_DATABASE_URL` antes de ejecutar las suites de integración y E2E

#### Scenario: La validación final deja evidencia reproducible
- **WHEN** el change se da por listo para aplicar o cerrar
- **THEN** existe evidencia de una corrida de tests relevante que cubre parser, importación, finalización y análisis
