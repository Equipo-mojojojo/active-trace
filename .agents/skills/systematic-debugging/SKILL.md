---
name: systematic-debugging
description: Proceso sistemático de debugging para active-trace. FastAPI async, SQLAlchemy, tests, logs estructurados.
license: MIT
---

# Systematic Debugging — active-trace

## Proceso — 5 pasos antes de tocar el código

```
1. REPRODUCIR   → ¿puedo fallar el test o el endpoint de forma consistente?
2. AISLAR       → ¿cuál es el mínimo código que reproduce el problema?
3. HIPÓTESIS    → ¿qué debería pasar vs qué pasa? (una hipótesis a la vez)
4. VERIFICAR    → test que confirma o refuta la hipótesis
5. CORREGIR     → mínimo cambio que hace pasar el test
```

## Diagnóstico de errores 422 (Pydantic)

```python
# El 422 trae detalle — leerlo siempre antes de debuggear
# Response body: {"detail": [{"loc": ["body", "campo"], "msg": "...", "type": "..."}]}

# Causas frecuentes:
# 1. extra='forbid' + campo no declarado en DTO
# 2. Tipo incorrecto (UUID string vs UUID object)
# 3. Campo requerido faltante
# 4. Validador custom que levanta ValueError
```

## Diagnóstico de errores 500 en endpoints async

```python
# Habilitar traceback completo en test:
import traceback

async def test_mi_endpoint(client_admin):
    r = client_admin.post("/api/recurso/", json={...})
    if r.status_code == 500:
        print(r.json())  # FastAPI incluye el traceback en dev mode
    assert r.status_code == 201
```

```python
# En main.py — asegurarse que DEBUG=True en test para ver tracebacks:
app = FastAPI(debug=settings.DEBUG)
```

## Diagnóstico de errores SQLAlchemy async

```python
# Error frecuente: "greenlet_spawn has not been called"
# Causa: acceder a relación lazy fuera de contexto async
# Fix: usar selectinload/joinedload en el query

# Error frecuente: "DetachedInstanceError"
# Causa: acceder al objeto ORM después de cerrar la sesión
# Fix: await db.refresh(objeto) antes de salir del contexto de sesión

# Error frecuente: "MissingGreenlet"
# Causa: mezclar código sync y async en SQLAlchemy
# Fix: todas las funciones que tocan DB deben ser async def
```

## Diagnóstico de tests que fallan por isolación de tenant

```python
# Síntoma: test pasa solo pero falla en suite completa
# Causa: datos de otro test "contaminan" el tenant de test
# Fix: verificar que el fixture db_session hace rollback entre tests

@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()  # ← esto debe estar
```

## Leer logs estructurados

```python
# Los logs son JSON — buscar por campos específicos:
# {"level": "ERROR", "message": "...", "tenant_id": "...", "trace_id": "..."}

# En tests — capturar logs:
def test_algo(caplog):
    import logging
    with caplog.at_level(logging.ERROR):
        # ejecutar código
        pass
    assert "texto esperado" not in caplog.text  # verificar que PII no aparezca
```

## Diagnóstico de migraciones Alembic

```bash
# Ver estado actual
alembic current

# Ver historial
alembic history --verbose

# Generar migración desde models (revisar SIEMPRE antes de aplicar)
alembic revision --autogenerate -m "descripcion"

# Aplicar
alembic upgrade head

# Revertir última
alembic downgrade -1
```

```python
# Error frecuente: "relation already exists"
# Causa: migración aplicada parcialmente
# Fix: alembic downgrade -1 && alembic upgrade head

# Error frecuente: columna de tipo enum ya existe
# Fix: usar IF NOT EXISTS en la migración
op.execute("CREATE TYPE IF NOT EXISTS estado_enum AS ENUM ('A', 'B')")
```

## Diagnóstico de workers async

```python
# Síntoma: worker procesa pero las comunicaciones no cambian de estado
# Verificar:
# 1. ¿Se está haciendo commit? (workers sí deben commitear — son procesos independientes)
# 2. ¿La sesión se cierra correctamente en cada iteración?
# 3. ¿El rollback en error está capturando la excepción correcta?

while True:
    async with session_factory() as session:
        try:
            await process_pending(session)
            await session.commit()    # ← workers SÍ commitean
        except Exception:
            await session.rollback()
            logger.exception("Worker falló")
    await asyncio.sleep(1)
```

## Checklist antes de abrir PR

```
[ ] El test falla antes del fix (RED confirmado)
[ ] El test pasa después del fix (GREEN confirmado)
[ ] No hay prints/breakpoints/console.log en el código
[ ] No hay secrets hardcodeados
[ ] Cobertura no bajó vs baseline
[ ] tenant_id en todos los queries nuevos
[ ] deleted_at.is_(None) en queries de datos activos
```
