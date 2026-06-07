---
name: python-testing-patterns
description: Patrones de testing con pytest async para active-trace. Fixtures, DB de test, TestClient, cobertura mínima.
license: MIT
---

# Python Testing Patterns — active-trace

## Setup mínimo

```bash
# Requiere TEST_DATABASE_URL apuntando a DB real de test
export TEST_DATABASE_URL="postgresql+asyncpg://activia:activia@localhost:5432/activia_trace_test"
python -m pytest tests -v
```

**Regla**: nunca mockear la DB. Tests de integración usan base real o contenedor efímero.

## Fixtures disponibles (conftest.py)

```python
# DB session aislada por test
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]: ...

# Tenant de test
@pytest_asyncio.fixture
async def tenant(db_session) -> Tenant: ...

# Usuario con rol específico
@pytest_asyncio.fixture
async def usuario_admin(db_session, tenant) -> User: ...

# TestClient con auth inyectada
@pytest_asyncio.fixture
async def client_admin(usuario_admin) -> TestClient: ...
```

## Template de test unitario (service/repository)

```python
import pytest
from uuid import uuid4


class TestMiService:
    """RED → GREEN → TRIANGULATE → REFACTOR"""

    async def test_crear_caso_base(self, db_session, tenant):
        """RED 1.1: crear con datos válidos retorna entidad persistida."""
        from app.services.mi_service import MiService
        from app.schemas.mi_schema import MiCreateDTO

        svc = MiService(db_session, tenant.id)
        dto = MiCreateDTO(nombre="Test")

        resultado = await svc.crear(dto)

        assert resultado.id is not None
        assert resultado.nombre == "Test"
        assert resultado.tenant_id == tenant.id

    async def test_crear_aislamiento_tenant(self, db_session, tenant):
        """TRIANGULATE: otro tenant no ve el registro."""
        from app.services.mi_service import MiService
        from app.schemas.mi_schema import MiCreateDTO

        otro_tenant_id = uuid4()
        svc_a = MiService(db_session, tenant.id)
        svc_b = MiService(db_session, otro_tenant_id)

        await svc_a.crear(MiCreateDTO(nombre="Solo de A"))
        items_b = await svc_b.listar()

        assert len(items_b) == 0
```

## Template de test de endpoint (router)

```python
class TestMiRouter:

    async def test_endpoint_requiere_auth(self, client_anonimo):
        """Sin JWT → 401."""
        response = client_anonimo.post("/api/v1/mi-recurso/", json={})
        assert response.status_code == 401

    async def test_endpoint_requiere_permiso(self, client_sin_permiso):
        """Sin permiso → 403."""
        response = client_sin_permiso.post("/api/v1/mi-recurso/", json={"nombre": "x"})
        assert response.status_code == 403

    async def test_crear_happy_path(self, client_admin):
        """Con permiso y datos válidos → 201."""
        response = client_admin.post("/api/v1/mi-recurso/", json={"nombre": "Nuevo"})
        assert response.status_code == 201
        assert response.json()["nombre"] == "Nuevo"

    async def test_schema_rechaza_campos_extra(self, client_admin):
        """extra='forbid' en schema → 422."""
        response = client_admin.post("/api/v1/mi-recurso/", json={"nombre": "x", "campo_extra": "y"})
        assert response.status_code == 422
```

## Cobertura mínima

```bash
python -m pytest tests --cov=app --cov-report=term-missing
# Mínimo: ≥80% líneas, ≥90% reglas de negocio
```

## Tests de seguridad obligatorios por módulo

```python
# 1. Aislamiento multi-tenant
async def test_tenant_isolation(self, ...):
    # Tenant A no ve datos de Tenant B

# 2. Identidad inmutable
async def test_identity_from_token_only(self, ...):
    # Pasar otro user_id en body no cambia el actor

# 3. Soft delete
async def test_soft_delete_no_hard_delete(self, ...):
    # Registro deleted_at != None sigue en DB

# 4. PII no aparece en logs
async def test_pii_not_in_logs(self, caplog, ...):
    # DNI/email no aparece en texto de logs
```

## Skip automático sin DB

```python
# conftest.py ya maneja esto — si no hay TEST_DATABASE_URL, los tests de DB se skipean
# No hace falta decorar cada test individualmente
```

## Nombrado de tests

```
test_{qué_hace}_{condición_o_caso}
test_crear_retorna_uuid
test_listar_filtra_por_tenant
test_login_rechaza_password_invalido
```
