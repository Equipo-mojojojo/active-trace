---
name: fastapi-templates
description: Patrones y templates para FastAPI + SQLAlchemy 2.0 async en active-trace. Routers, dependencies, schemas, estructura de endpoints, manejo de errores.
license: MIT
---

# FastAPI Templates — active-trace

## Estructura de un Router

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.mi_schema import MiCreateDTO, MiResponseDTO
from app.services.mi_service import MiService

router = APIRouter(prefix="/api/v1/mi-recurso", tags=["mi-recurso"])


@router.post("/", response_model=MiResponseDTO, status_code=status.HTTP_201_CREATED)
async def crear(
    body: MiCreateDTO,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("modulo:accion")),
    db: AsyncSession = Depends(get_db),
) -> MiResponseDTO:
    svc = MiService(db, current_user.tenant_id)
    return await svc.crear(body)
```

## Reglas de Routers

- **Sin lógica de negocio** — el router solo valida entrada, llama al service, retorna DTO
- **Identidad siempre del JWT** — `current_user = Depends(get_current_user)`, nunca de params
- **RBAC en cada endpoint** — `Depends(require_permission("modulo:accion"))` obligatorio
- **tenant_id del JWT** — `current_user.tenant_id`, nunca del body/URL

## Estructura de un Schema (Pydantic v2)

```python
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID


class MiCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")  # SIEMPRE

    nombre: str
    descripcion: str | None = None


class MiResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    nombre: str
    # NUNCA incluir PII sin cifrar en response DTOs
```

## Dependency Injection Pattern

```python
# Service instanciado por request con session + tenant_id
svc = MiService(db, current_user.tenant_id)

# Repository instanciado dentro del service
repo = MiRepository(db, tenant_id)
```

## Manejo de Errores

```python
from app.core.exceptions import NotFoundError, ConflictError

# En services — lanzar excepciones del dominio
raise NotFoundError(f"Recurso {id} no encontrado")
raise ConflictError("Ya existe un recurso con ese nombre")

# FastAPI convierte automáticamente via exception handlers en main.py
```

## Registro en main.py

```python
from app.api.v1.routers import mi_router

app.include_router(mi_router.router)
```

## Patrones de Paginación

```python
@router.get("/", response_model=list[MiResponseDTO])
async def listar(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    ...
)
```

## Upload de Archivos

```python
from fastapi import UploadFile, File

@router.post("/import")
async def importar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("modulo:importar")),
    db: AsyncSession = Depends(get_db),
):
    contenido = await file.read()
    # Pasar bytes al service — nunca procesar en router
    svc = MiService(db, current_user.tenant_id)
    return await svc.importar(contenido, file.filename)
```
