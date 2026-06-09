---
name: api-security-best-practices
description: Patrones de seguridad para APIs FastAPI en active-trace. JWT, RBAC, multi-tenancy, PII, rate limiting, OWASP.
license: MIT
---

# API Security Best Practices — active-trace

## Regla de Oro: Identidad siempre del JWT

```python
# CORRECTO — identidad del token verificado
@router.get("/recurso/{id}")
async def ver(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # tenant_id del JWT, nunca del path/body/header
    svc = MiService(db, current_user.tenant_id)

# INCORRECTO — nunca hacer esto
@router.get("/recurso/{id}")
async def ver(id: UUID, tenant_id: UUID, user_id: UUID):  # ← inyección de identidad
    ...
```

## RBAC en cada endpoint — fail-closed

```python
# Todo endpoint declara su permiso. Sin permiso → 403 automático.
@router.post("/comunicaciones/")
async def enviar(
    body: ComunicacionCreateDTO,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("comunicacion:enviar")),  # OBLIGATORIO
    db: AsyncSession = Depends(get_db),
):
    ...

# Permiso (propio) — el usuario solo ve sus propios recursos
@router.get("/mis-tareas/")
async def mis_tareas(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("tareas:ver:propio")),
    db: AsyncSession = Depends(get_db),
):
    svc = TareaService(db, current_user.tenant_id)
    return await svc.listar_por_usuario(current_user.id)
```

## Multi-tenancy — row-level obligatorio

```python
# Repository siempre filtra por tenant — nunca query sin scope
class MiRepository(BaseRepository):
    async def listar(self) -> list[MiModelo]:
        # BaseRepository ya aplica WHERE tenant_id = self.tenant_id
        result = await self.db.execute(
            select(MiModelo).where(MiModelo.tenant_id == self.tenant_id)
        )
        return result.scalars().all()

    async def get_by_id(self, id: UUID) -> MiModelo | None:
        result = await self.db.execute(
            select(MiModelo).where(
                MiModelo.id == id,
                MiModelo.tenant_id == self.tenant_id,  # SIEMPRE
                MiModelo.deleted_at.is_(None),          # soft delete
            )
        )
        return result.scalar_one_or_none()
```

## PII — nunca en texto plano

```python
from app.core.encryption import encrypt, decrypt

class Usuario(Base, TenantScopedModelMixin):
    _email_enc: Mapped[str] = mapped_column("email", EncryptedString())
    _dni_enc:   Mapped[str | None] = mapped_column("dni", EncryptedString())
    _cbu_enc:   Mapped[str | None] = mapped_column("cbu", EncryptedString())

# En Response DTOs — nunca exponer PII cruda
class UsuarioResponseDTO(BaseModel):
    id: UUID
    nombre: str
    email: str          # desencriptado por el service, nunca exponer _enc
    # dni: str          # ← NO incluir si no es necesario para el caller
```

## Validación de entrada — Pydantic + extra='forbid'

```python
class ComunicacionCreateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rechaza campos no declarados

    asunto: str = Field(min_length=1, max_length=255)
    cuerpo: str = Field(min_length=1)
    destinatario_ids: list[UUID] = Field(min_length=1, max_length=500)

    @field_validator("asunto")
    @classmethod
    def sanitizar_asunto(cls, v: str) -> str:
        return v.strip()
```

## Rate limiting — endpoints críticos

```python
# Aplicado en auth (ya implementado en C-03)
# Patrón para otros endpoints sensibles:
from app.core.rate_limit import RateLimiter

@router.post("/api/auth/login")
async def login(
    body: LoginDTO,
    limiter: RateLimiter = Depends(get_rate_limiter("5/60s")),
):
    ...
```

## Headers de seguridad

```python
# En main.py — ya configurado en C-01, verificar que esté activo
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
```

## Soft delete — nunca hard delete

```python
# CORRECTO
async def eliminar(self, id: UUID) -> None:
    entidad = await self.repo.get_by_id(id)
    if not entidad:
        raise NotFoundError(f"{id}")
    entidad.deleted_at = datetime.utcnow()
    await self.db.flush()

# INCORRECTO
await self.db.delete(entidad)  # ← nunca
```

## Tests de seguridad obligatorios

```python
async def test_requiere_autenticacion(self, client_anonimo):
    r = client_anonimo.post("/api/recurso/", json={})
    assert r.status_code == 401

async def test_requiere_permiso(self, client_sin_permiso):
    r = client_sin_permiso.post("/api/recurso/", json={"nombre": "x"})
    assert r.status_code == 403

async def test_aislamiento_tenant(self, db_session, tenant_a, tenant_b):
    # Tenant A crea recurso → Tenant B no lo ve
    ...

async def test_identidad_inmutable(self, client_admin, otro_user_id):
    # Pasar user_id en body no cambia el actor del registro
    r = client_admin.post("/api/recurso/", json={"user_id": str(otro_user_id)})
    assert r.status_code == 422  # extra='forbid'
```
