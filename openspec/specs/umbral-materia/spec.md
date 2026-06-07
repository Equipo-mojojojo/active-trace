## ADDED Requirements

### Requirement: UmbralMateria is isolated per assignment
Each `UmbralMateria` row SHALL be scoped to a single `Asignacion` (docente × materia × period). Changing the threshold for one assignment SHALL NOT affect grades or thresholds of other assignments for the same materia.

#### Scenario: Threshold update does not affect other assignments
- **WHEN** a PROFESOR updates `UmbralMateria.umbral_pct` for their assignment
- **THEN** the threshold of another docente's assignment for the same materia remains unchanged

### Requirement: Default threshold is 60 percent
When no `UmbralMateria` exists for an assignment, the system SHALL apply a default threshold of `60` percent for numeric grades.

#### Scenario: No UmbralMateria falls back to default
- **WHEN** a `Calificacion` is computed for an assignment without a configured `UmbralMateria`
- **THEN** `aprobado` is derived using `umbral_pct=60`

### Requirement: Textual approved values are configurable per assignment
`UmbralMateria.valores_aprobatorios` SHALL store the list of textual grade values that count as approved. The default SHALL be `["Satisfactorio", "Supera lo esperado"]` (RN-02).

#### Scenario: Custom textual approved value is respected
- **WHEN** `UmbralMateria.valores_aprobatorios=["Aprobado"]` and a `Calificacion` has `nota_textual="Aprobado"`
- **THEN** `aprobado` is set to `True`

#### Scenario: Default textual approved values apply when list is empty
- **WHEN** `UmbralMateria` has no `valores_aprobatorios` configured
- **THEN** `["Satisfactorio", "Supera lo esperado"]` are used as the approved set

### Requirement: PROFESOR can configure threshold via API
The system SHALL expose an endpoint that allows a PROFESOR to create or update the `UmbralMateria` for their own assignment. A COORDINADOR SHALL be able to configure it for any assignment in the tenant.

#### Scenario: PROFESOR sets threshold for own assignment
- **WHEN** a PROFESOR sends `PUT /api/v1/calificaciones/umbral` with `asignacion_id` belonging to them and `umbral_pct=75`
- **THEN** the system creates or updates the `UmbralMateria` row and returns `200`

#### Scenario: PROFESOR cannot set threshold for another docente's assignment
- **WHEN** a PROFESOR sends a threshold update for an `asignacion_id` that belongs to a different docente
- **THEN** the system returns `403`
