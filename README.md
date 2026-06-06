# active-trace

Plataforma de gestión académica y trazabilidad multi-tenant. Opera como capa de orquestación sobre Moodle: consolida calificaciones, detecta atrasos, gestiona comunicación saliente, equipos docentes, encuentros, coloquios y auditoría completa.

---

## Requisitos previos

- Python 3.13+
- Docker Desktop (para la base de datos)
- Git

---

## Setup inicial

### 1. Clonar y pararse en la rama correcta

```bash
git clone https://github.com/Equipo-mojojojo/active-trace.git
cd active-trace
git checkout clari
```

### 2. Instalar dependencias del backend

```bash
cd backend
pip install -e ".[test]"
```

### 3. Crear el archivo `.env`

Crear `backend/.env` con este contenido:

```env
DATABASE_URL=postgresql+asyncpg://activia:activia@localhost:5432/activia_trace
TEST_DATABASE_URL=postgresql+asyncpg://activia:activia@localhost:5432/activia_trace_test
SECRET_KEY=dev-secret-key-change-me-in-production-32chars
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=10080
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES=5
TOTP_ISSUER=activia-trace
LOGIN_RATE_LIMIT_MAX_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
LOG_LEVEL=INFO
OTEL_ENABLED=false
OTEL_SERVICE_NAME=activia-trace-api
OTEL_EXPORTER_OTLP_ENDPOINT=
```

### 4. Levantar la base de datos

```bash
# Desde la raíz del proyecto
docker-compose up -d postgres
```

### 5. Crear la base de datos de test y correr migraciones

```bash
# Crear la DB de test
docker exec active-trace-postgres-1 psql -U activia -d activia_trace -c "CREATE DATABASE activia_trace_test;"

# Correr migraciones (desde backend/)
cd backend
python -m alembic upgrade head
```

### 6. Correr los tests

```bash
# Desde backend/
$env:TEST_DATABASE_URL="postgresql+asyncpg://activia:activia@localhost:5432/activia_trace_test"
python -m pytest tests -v
```

Resultado esperado: **267+ passed** (aumenta con cada change implementado).

---

## Levantar la API completa

```bash
# Desde la raíz del proyecto
docker-compose up --build
```

La API queda disponible en:
- `http://localhost:8000` — API
- `http://localhost:8000/docs` — Swagger UI

### Worker de comunicaciones (C-12)

El worker de despacho corre como proceso separado:

```bash
# Desde backend/
python -m app.workers.main
```

Variables de entorno opcionales del worker:
```env
WORKER_MAX_RETRIES=3    # reintentos antes de marcar Error (default: 3)
```

---

## Estructura del proyecto

```
active-trace/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/   # Endpoints (sin lógica de negocio)
│   │   ├── core/             # Config, seguridad, auth, permisos, OTel
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Acceso a DB (siempre con scope de tenant)
│   │   ├── schemas/          # DTOs Pydantic (request/response)
│   │   ├── services/         # Lógica de negocio
│   │   ├── integrations/     # Cliente Moodle WS
│   │   └── workers/          # Background jobs
│   ├── alembic/              # Migraciones de base de datos
│   └── tests/                # Suite de tests
├── openspec/                 # Artefactos de diseño (proposals, specs, tasks)
├── knowledge-base/           # Documentación de dominio
├── docs/                     # Arquitectura y PRD
└── docker-compose.yml
```

---

## Changes implementados

| Change | Descripción | Estado |
|--------|-------------|--------|
| C-01 | Foundation setup (FastAPI, Docker, OTel) | Archivado |
| C-02 | Core models y tenancy (mixins, repo base, AES-256) | Archivado |
| C-03 | Auth JWT + 2FA (login, refresh, recuperación) | Archivado |
| C-04 | RBAC permisos finos (roles, permisos `modulo:accion`) | Completo |
| C-05 | Audit log (append-only, impersonación) | Completo |
| C-06 | Estructura académica (Carrera, Cohorte, Materia) | Completo |
| C-07 | Usuarios y asignaciones (PII cifrada, vigencia) | Completo |
| C-08 | Equipos docentes | Completo |
| C-09 | Padrón e ingesta Moodle | Completo |
| C-10 | Calificaciones y umbral | Completo |
| C-11 | Análisis atrasados y reportes | Completo |
| C-12 | Comunicaciones salientes + cola worker | Completo |

Próximo: **C-13** encuentros/coloquios, **C-21** frontend shell.

---

## Reglas del proyecto (resumen)

- Identidad **siempre** desde el JWT — nunca desde parámetros de URL o body
- Todo query en repositories **siempre** filtra por `tenant_id`
- Cada endpoint protegido declara `require_permission("modulo:accion")`
- Flujo unidireccional: `Routers → Services → Repositories → Models`
- Soft delete siempre — nunca hard delete
- PII (DNI, CUIL, CBU, email) siempre cifrada con AES-256
- Tests sin mocks de DB — siempre contra base real

Ver [CLAUDE.md](CLAUDE.md) para las reglas completas y [CHANGES.md](CHANGES.md) para el roadmap.
