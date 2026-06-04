## ADDED Requirements

### Requirement: Calificacion model persists grade per student-activity
The system SHALL store one `Calificacion` row per `(tenant_id, entrada_padron_id, actividad)`. Each row holds the numeric grade (`nota_numerica`), the textual grade (`nota_textual`), or both. The `aprobado` field SHALL be computed at write time using the active `UmbralMateria` for the related assignment and persisted — it SHALL NOT be recalculated when the threshold changes later.

#### Scenario: Numeric grade above threshold is approved
- **WHEN** a `Calificacion` is created with `nota_numerica=75` and the active `UmbralMateria.umbral_pct=60`
- **THEN** `aprobado` is set to `True`

#### Scenario: Numeric grade below threshold is not approved
- **WHEN** a `Calificacion` is created with `nota_numerica=50` and the active `UmbralMateria.umbral_pct=60`
- **THEN** `aprobado` is set to `False`

#### Scenario: Textual grade in approved set is approved
- **WHEN** a `Calificacion` is created with `nota_textual="Satisfactorio"` and no `nota_numerica`
- **THEN** `aprobado` is set to `True`

#### Scenario: Textual grade outside approved set is not approved
- **WHEN** a `Calificacion` is created with `nota_textual="No satisfactorio"` and no `nota_numerica`
- **THEN** `aprobado` is set to `False`

#### Scenario: Numeric grade takes precedence when both fields present
- **WHEN** a `Calificacion` is created with both `nota_numerica=80` and `nota_textual="No satisfactorio"` and `UmbralMateria.umbral_pct=60`
- **THEN** `aprobado` is set to `True` (numeric wins)

### Requirement: Calificacion upsert is idempotent per student-activity
Re-importing the same grade for the same student and activity SHALL update the existing row, not create a duplicate.

#### Scenario: Re-import same activity updates existing record
- **WHEN** a `Calificacion` already exists for `(entrada_padron_id, actividad)` and a new import provides a different `nota_numerica` for the same pair
- **THEN** the existing row is updated with the new value and `aprobado` is recomputed

### Requirement: Calificacion origin is tracked
The system SHALL record whether a grade was imported from an LMS file (`Importado`) or entered manually (`Manual`).

#### Scenario: Imported grade has correct origin
- **WHEN** a `Calificacion` is created via the import endpoint
- **THEN** `origen` is set to `"Importado"`
