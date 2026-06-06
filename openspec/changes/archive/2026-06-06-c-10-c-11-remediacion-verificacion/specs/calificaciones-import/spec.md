## ADDED Requirements

### Requirement: Importación y preview resuelven alumnos contra el padrón versionado válido
Los flujos `POST /api/v1/calificaciones/preview` y `POST /api/v1/calificaciones/import` SHALL resolver alumnos usando el padrón versionado válido del tenant para la materia solicitada, siguiendo el vínculo `VersionPadron` → `EntradaPadron` y sin depender de columnas académicas inexistentes en `EntradaPadron`.

#### Scenario: Importación usa entradas del padrón activo real
- **WHEN** existe una versión activa de padrón válida para la materia en el contexto solicitado
- **THEN** el import cruza alumnos exclusivamente contra las `EntradaPadron` pertenecientes a esa versión válida

#### Scenario: El import no asume `materia_id` directo en EntradaPadron
- **WHEN** el service resuelve alumnos para importar calificaciones
- **THEN** la implementación obtiene el contexto académico a través de `VersionPadron` y no leyendo un campo inexistente en `EntradaPadron`

#### Scenario: Padrón no correspondiente no participa del cruce
- **WHEN** existen entradas históricas o de otra versión/corte académico del mismo tenant
- **THEN** el import no las usa para mapear alumnos de la corrida actual
