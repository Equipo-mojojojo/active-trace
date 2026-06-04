## ADDED Requirements

### Requirement: Ranking excludes students with zero approved activities
The ranking SHALL list students ordered descending by count of `Calificacion` rows with `aprobado=True`. Students with zero approved activities SHALL NOT appear (RN-09).

#### Scenario: Student with one approved activity appears in ranking
- **WHEN** student A has exactly one `Calificacion` with `aprobado=True`
- **THEN** student A appears in the ranking with count=1

#### Scenario: Student with zero approved activities is excluded
- **WHEN** student B has no `Calificacion` with `aprobado=True`
- **THEN** student B does NOT appear in the ranking

#### Scenario: Ranking is ordered descending by approved count
- **WHEN** student A has 5 approved and student B has 3 approved
- **THEN** student A appears before student B in the ranking response

### Requirement: Reporte rapido provides key materia metrics
`GET /api/v1/analisis/reporte` SHALL return for a given materia: total students, count of students with ≥1 approved activity, count of atrasados, and a list of activities sorted by approval rate ascending (worst-performing first).

#### Scenario: Reporte shows correct totals
- **WHEN** a materia has 10 students, 6 with ≥1 approved and 4 atrasados
- **THEN** reporte returns `total=10`, `con_aprobadas=6`, `atrasados=4`

#### Scenario: Empty materia returns zeroes
- **WHEN** a materia has no calificaciones
- **THEN** reporte returns zeros and empty activity list

### Requirement: Notas finales groups selected activities per student
`GET /api/v1/analisis/notas-finales` SHALL accept a list of activity names and return, per student, the average of `nota_numerica` for those activities. Students with no numeric grades for any selected activity are omitted.

#### Scenario: Average computed over selected activities
- **WHEN** student A has `nota_numerica=80` for TP1 and `nota_numerica=60` for TP2, and both are selected
- **THEN** the response shows `nota_final=70` for student A

#### Scenario: Textual-only grades do not contribute to nota final
- **WHEN** student A has only `nota_textual` grades for the selected activities
- **THEN** student A is omitted from the notas finales response
