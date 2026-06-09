## ADDED Requirements

### Requirement: Lista de encuentros con vista admin global
El sistema SHALL mostrar la lista global de encuentros (slots e instancias) de toda la institución. El COORDINADOR/ADMIN SHALL poder ver encuentros de todas las comisiones, no solo las propias.

#### Scenario: Vista global de encuentros
- **WHEN** un COORDINADOR navega a `/encuentros`
- **THEN** ve la tabla con todos los encuentros de la institución, con columnas: materia, cohorte, docente, tipo (Recurrente/Único), próxima instancia, estado (badge), meet_url

### Requirement: Crear encuentro recurrente o único
El sistema SHALL permitir crear un encuentro desde un modal con los siguientes campos: materia (select), cohorte (select), tipo (Recurrente/Único), día de la semana y hora (para recurrente) o fecha específica (para único), meet_url (opcional), cantidad de semanas (para recurrente). Al crear un encuentro recurrente, el backend genera todas las instancias del slot.

#### Scenario: Crear encuentro recurrente
- **WHEN** el usuario selecciona tipo "Recurrente", elige día/hora y cantidad de semanas y guarda
- **THEN** el sistema crea el slot con todas sus instancias y la lista se actualiza

#### Scenario: Crear encuentro único
- **WHEN** el usuario selecciona tipo "Único", elige una fecha específica y guarda
- **THEN** el sistema crea una sola instancia y la lista se actualiza

### Requirement: Editar instancia de encuentro
El sistema SHALL permitir editar una instancia individual de encuentro: estado (Programado/Realizado/Cancelado), meet_url, video_url (grabación posterior), y comentario. La edición no SHALL afectar otras instancias del mismo slot.

#### Scenario: Editar estado de instancia
- **WHEN** el COORDINADOR hace click en una instancia y cambia su estado a "Realizado"
- **THEN** solo esa instancia se actualiza; las demás del mismo slot no cambian

#### Scenario: Agregar meet_url a instancia
- **WHEN** el usuario agrega o edita la meet_url de una instancia y guarda
- **THEN** el link queda registrado y visible en la tabla

### Requirement: Registro y consulta de guardias
El sistema SHALL mostrar la lista de guardias registradas por tutores, con filtros por período y docente. El COORDINADOR SHALL poder exportar el listado.

#### Scenario: Lista de guardias
- **WHEN** un COORDINADOR navega a `/encuentros/guardias`
- **THEN** ve la tabla con guardias (docente, fecha/hora, comisión, observación)

#### Scenario: Export de guardias
- **WHEN** el usuario hace click en "Exportar"
- **THEN** el navegador descarga un CSV con las guardias visibles
