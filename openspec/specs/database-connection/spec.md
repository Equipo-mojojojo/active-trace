## ADDED Requirements

### Requirement: Engine y sesión async de SQLAlchemy 2.0

El sistema SHALL configurar un engine async de SQLAlchemy 2.0 usando el driver `asyncpg` sobre PostgreSQL, junto con una factory de sesiones async (`async_sessionmaker`). El acceso a datos SHALL realizarse exclusivamente mediante sesiones async producidas por esta factory. La misma infraestructura SHALL soportar metadata de modelos, migraciones Alembic y acceso tenant-aware sobre las entidades base del sistema.

#### Scenario: Engine async inicializado

- **WHEN** la aplicación inicia con un `DATABASE_URL` válido apuntando a PostgreSQL vía asyncpg
- **THEN** el engine async se crea y es capaz de abrir una conexión

#### Scenario: Conexión a base de datos de test

- **WHEN** se ejecuta el smoke test de conexión contra una base de datos de test
- **THEN** una sesión async puede ejecutar una consulta trivial (p. ej. `SELECT 1`) y obtener resultado

#### Scenario: Metadata base disponible para migraciones y modelos

- **WHEN** la capa de persistencia registra el modelo `Tenant` y los mixins base del sistema
- **THEN** la metadata compartida queda disponible para generar y ejecutar migraciones Alembic coherentes

### Requirement: Sesión por request vía dependency injection

El sistema SHALL proveer una dependency de FastAPI que abra una sesión async por request, la inyecte en los handlers que la requieran y garantice su cierre al finalizar la request (incluso ante excepción). Cada request SHALL recibir su propia sesión aislada; las sesiones NO SHALL compartirse entre requests.

#### Scenario: Una sesión por request

- **WHEN** llega una request que depende de la sesión de base de datos
- **THEN** la dependency provee una sesión async dedicada a esa request
- **AND** la sesión se cierra al terminar la request

#### Scenario: Cierre ante error

- **WHEN** un handler que usa la sesión lanza una excepción
- **THEN** la sesión se cierra correctamente sin filtrar la conexión al pool
