# active-trace

Plataforma de gestión académica y trazabilidad multi-tenant sobre Moodle.

---

## Requisitos

- Docker Desktop
- Node.js 20+
- Python 3.13

---

## Levantar el proyecto

### Terminal 1 — Backend (Docker)

> ⚠️ Correr desde la **raíz del proyecto** (`active-trace/`), donde está el `docker-compose.yml`.

```powershell
cd active-trace
docker-compose up
```

Levanta PostgreSQL, la API (FastAPI en puerto 8000) y el worker de comunicaciones.

### Terminal 2 — Entorno virtual Python

Solo la **primera vez**:

```powershell
cd active-trace/backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Las veces siguientes:

```powershell
cd active-trace/backend
.venv\Scripts\activate
```

> El Docker debe estar corriendo para que la DB esté disponible en `localhost:5432`.

### Terminal 3 — Frontend

```powershell
cd active-trace/frontend
npm install   # solo la primera vez
npm run dev
```

Abre `http://localhost:5173`.

---

## Variables de entorno

Antes de correr el proyecto, verificá que `backend/.env` exista con el valor correcto de `SECRET_KEY`. Este valor **debe coincidir** con el que usa Docker, de lo contrario el login falla para todos los usuarios que no sean admin.

Valor requerido en `backend/.env`:

```
SECRET_KEY=replace-with-a-secret-key-of-at-least-32-characters
```

> ⚠️ Si alguna vez cambiás el `SECRET_KEY` después de haber corrido el seed, los usuarios quedan con un hash inválido. Corrés `python -m scripts.reset_users` y después `python -m scripts.seed_dev` para recrearlos.

---

## Migrations y seed (primera vez)

Con el entorno virtual activado y Docker corriendo:

```powershell
cd backend
.venv\Scripts\activate

# Aplicar migraciones
alembic upgrade head

# Crear usuarios de dev
python -m scripts.seed_dev
```

Credenciales de dev:

| Rol          | Email                    | Password      |
|--------------|--------------------------|---------------|
| ADMIN        | admin@demo.com           | Admin1234!    |
| PROFESOR     | profesor@demo.com        | Profesor1234! |
| COORDINADOR  | coordinador@demo.com     | Coord1234!    |
| FINANZAS     | finanzas@demo.com        | Finanzas1234! |

---

## Correr tests

```powershell
cd backend
.venv\Scripts\activate
python -m pytest tests/
```

---

## Stack

| Capa       | Tecnología                          |
|------------|-------------------------------------|
| Backend    | Python 3.13 · FastAPI · SQLAlchemy  |
| Base datos | PostgreSQL (Docker)                 |
| Frontend   | React 18 · TypeScript · Vite        |
| Estilos    | Tailwind CSS v4                     |
| Auth       | JWT + httpOnly cookie               |
