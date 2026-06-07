---
name: test-driven-development
description: Ciclo TDD estricto para active-trace. RED → GREEN → TRIANGULATE → REFACTOR. Aplica a toda implementación de tasks en el flujo opsx:apply.
license: MIT
---

# Test-Driven Development — active-trace

## Las tres leyes

1. **No escribir código de producción** hasta tener un test que falla
2. **No escribir más test** del mínimo necesario para fallar
3. **No escribir más código** del mínimo para pasar el test

## El ciclo por cada task

```
SAFETY NET → RED → GREEN → TRIANGULATE → REFACTOR → ✅
```

### 0. Safety Net (si modificás archivos existentes)

```bash
python -m pytest tests/test_archivo_afectado.py -v
# Capturar baseline: "N tests passing"
# Si alguno falla → STOP, reportar como "falla preexistente"
```

### 1. RED — Escribir el test primero

```python
# El test referencia código que NO EXISTE AÚN
async def test_comunicacion_pasa_a_enviado_al_despachar(self, db_session, tenant):
    """RED: worker transiciona Pendiente → Enviado."""
    from app.services.comunicacion_service import ComunicacionService  # no existe aún
    
    svc = ComunicacionService(db_session, tenant.id)
    com = await svc.crear(...)
    
    await svc.despachar(com.id)
    
    actualizado = await svc.get(com.id)
    assert actualizado.estado == "Enviado"
```

**Ejecutar → debe FALLAR** (ImportError o AssertionError). Si pasa sin código → el test está mal.

### 2. GREEN — Mínimo código para pasar

```python
# Implementar SOLO lo necesario para que el test pase
# Fake It es válido aquí:
async def despachar(self, id: UUID) -> None:
    com = await self.repo.get(id)
    com.estado = "Enviado"  # hardcoded está bien en GREEN
    await self.repo.save(com)
```

**Ejecutar → debe PASAR**.

### 3. TRIANGULATE — Segundo caso diferente

```python
# Agregar caso con inputs/outputs distintos
async def test_comunicacion_con_error_pasa_a_error(self, db_session, tenant):
    """TRIANGULATE: worker maneja error de envío → estado Error."""
    svc = ComunicacionService(db_session, tenant.id)
    com = await svc.crear(...)
    
    await svc.despachar(com.id, simular_error=True)
    
    actualizado = await svc.get(com.id)
    assert actualizado.estado == "Error"
```

Si el Fake It se rompe → generalizar la lógica real.

**Mínimo**: 2 casos por comportamiento (happy path + 1 edge case).

### 4. REFACTOR — Mejorar sin cambiar comportamiento

```python
# Extraer constantes, mejorar nombres, eliminar duplicación
# Ejecutar tests después de CADA cambio de refactor
```

**Tests deben seguir pasando después de cada paso**.

## Aplicado a estados de worker (C-12)

Los estados `Pendiente → Enviando → Enviado/Error/Cancelado` son perfectos para TDD:

```python
# RED: test que describe la transición
async def test_transicion_pendiente_a_enviando(self, ...): ...
async def test_transicion_enviando_a_enviado_ok(self, ...): ...
async def test_transicion_enviando_a_error_en_fallo(self, ...): ...
async def test_cancelar_solo_desde_pendiente(self, ...): ...
async def test_cancelar_desde_enviando_falla(self, ...): ...
```

## Evidencia requerida en el resumen

Al terminar cada task, reportar:

```
| Task | Test file | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|------------|-----|-------|-------------|----------|
| 1.1  | test_X.py | ✅ 5/5    | ✅  | ✅    | ✅ 3 casos  | ✅       |
```

## Anti-patrones a evitar

```python
# ❌ Assertion tautológica
assert True

# ❌ Test que no puede fallar
assert resultado is not None  # si resultado siempre existe

# ❌ Escribir código antes del test
# ❌ Saltear triangulación cuando el spec tiene múltiples escenarios
# ❌ Mockear la DB (regla dura del proyecto)
```

## Cuándo un test es suficientemente bueno

- Describe un comportamiento del spec (no un detalle de implementación)
- Falla cuando la implementación está mal
- Pasa cuando la implementación es correcta
- Es repetible y no depende de orden de ejecución
