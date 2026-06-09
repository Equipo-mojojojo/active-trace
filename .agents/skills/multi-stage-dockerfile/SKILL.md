---
name: multi-stage-dockerfile
description: Patrones Docker multi-stage para active-trace. FastAPI backend, React frontend, docker-compose, Easypanel.
license: MIT
---

# Multi-Stage Dockerfile — active-trace

## Backend — FastAPI (Python 3.13)

```dockerfile
# backend/Dockerfile
FROM python:3.13-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Stage: dependencias
FROM base AS deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage: producción
FROM base AS production
COPY --from=deps /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

# Usuario no-root para seguridad
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Frontend — React + Vite

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --frozen-lockfile

# Stage: build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage: producción con nginx
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# frontend/nginx.conf — SPA routing
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA routing
    }
    location /api/ {
        proxy_pass http://backend:8000;    # proxy al backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## docker-compose — desarrollo local

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: activia
      POSTGRES_PASSWORD: activia
      POSTGRES_DB: activia_trace
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U activia"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      target: production
    environment:
      DATABASE_URL: postgresql+asyncpg://activia:activia@db:5432/activia_trace
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  worker:
    build:
      context: ./backend
      target: production
    command: python -m app.workers.main
    environment:
      DATABASE_URL: postgresql+asyncpg://activia:activia@db:5432/activia_trace
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      target: production
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## docker-compose — test (DB efímera)

```yaml
# docker-compose.test.yml
services:
  db_test:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: activia
      POSTGRES_PASSWORD: activia
      POSTGRES_DB: activia_trace_test
    tmpfs:
      - /var/lib/postgresql/data   # en memoria — más rápido y descartable

  backend_test:
    build:
      context: ./backend
    command: >
      sh -c "alembic upgrade head &&
             python -m pytest tests -v --cov=app --cov-report=term-missing"
    environment:
      DATABASE_URL: postgresql+asyncpg://activia:activia@db_test:5432/activia_trace_test
      TEST_DATABASE_URL: postgresql+asyncpg://activia:activia@db_test:5432/activia_trace_test
    depends_on:
      - db_test
```

## Easypanel — convenciones de deploy

```yaml
# Variables de entorno requeridas en Easypanel (nunca en el repo):
# DATABASE_URL        ← apunta a la instancia de Postgres del proyecto
# SECRET_KEY          ← 64 chars random, hex
# ENCRYPTION_KEY      ← 32 bytes base64 para AES-256
# LOG_LEVEL           ← INFO en prod
# ALLOWED_HOSTS       ← dominio del deploy
# DEBUG               ← false en prod
```

## Reglas

- **Nunca `latest` como tag** — usar versiones fijas (`postgres:16-alpine`, `node:20-alpine`)
- **Usuario no-root** en producción (`adduser appuser`)
- **Secrets vía variables de entorno**, nunca en el Dockerfile ni en el repo
- **Healthcheck en todos los servicios** que otros servicios esperan
- **`tmpfs` en tests** para DB efímera — más rápido y sin cleanup manual
- **`target: production`** explícito en docker-compose para no levantar el stage de deps
