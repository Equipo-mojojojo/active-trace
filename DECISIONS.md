# DECISIONS.md — Decisiones de diseño y contexto del proyecto

> Este archivo documenta las decisiones de diseño, convenciones y descubrimientos técnicos tomados durante el desarrollo. Es la memoria del equipo — leelo antes de tocar un módulo existente.

---

## Preguntas abiertas cerradas

### PA-22 — Claves de Plus (liquidaciones)
**Decisión**: NO hardcodear claves (PROG, BD, etc.) en código.

- Se agrega campo `grupo_plus_clave TEXT NULL` en la tabla `materia`.
- Si `grupo_plus_clave` es null → la materia no genera plus.
- La entidad `SalarioPlus(grupo, rol, tenant_id, monto, desde, hasta)` es el lookup en DB.
- **Completamente configurable por interfaz**, sin tocar código.

### PA-23 — Acumulación de Plus
**Decisión**: Fórmula lineal (RN-34) con tope opcional.

```
total = salario_base_rol + Σ plus(comision.grupo_plus_clave, rol)
```
- Acumula **por comisión** — cada comisión activa suma su plus independientemente.
- Tope opcional: campo `tope_plus INTEGER NULL` en `Tenant`. Si null → sin tope.
- Si `tope_plus = 2` → solo se acumulan los plus de las primeras 2 comisiones con grupo.
- La lógica vive en `calcular_total()` en `liquidacion_service.py` — función pura testeable.

---

## C-18 — Liquidaciones y Honorarios

### Diseño del motor de cálculo
La lógica de cálculo y segmentación es **funciones puras** (sin DB), testeable sin fixtures:

```python
# backend/app/services/liquidacion_service.py
calcular_total(salario_base, comisiones, plus_lookup, rol, tenant) → (monto_base, monto_plus)
segmentar_liquidaciones(liquidaciones) → SimpleNamespace(general, nexo, facturantes, total_sin_factura, total_con_factura)
```

### Decisiones técnicas
| Decisión | Alternativa descartada | Razón |
|----------|----------------------|-------|
| `grupo_plus_clave` en `Materia` (campo nullable) | Tabla intermedia `materia_plus_clave` | Relación 1-a-1, un join extra sin beneficio |
| `tope_plus` en `Tenant` | `tope` por `(grupo, rol)` en `SalarioPlus` | Regla actual no diferencia por grupo — KISS |
| `vigencias_solapan()` como función libre en `salario_base_repository.py` | Constraint DB | Más flexible, reutilizable, testeable |
| `Liquidacion.comisiones` como JSONB | Tabla pivot `liquidacion_comision` | Es snapshot inmutable; no se necesita querying posterior |
| `Factura.archivo_path` (path en disco) | BLOB en DB | Performance; permite cambiar backend de storage sin migración |
| Una sola migración 0016 atómica | Varias migraciones pequeñas | Módulo cohesionado, sin changes que dependan parcialmente |
| Guard de cierre en `LiquidacionRepository.update()` | Solo en router | Doble seguridad — inmutabilidad garantizada en la capa de datos |

### Validación de solapamiento de vigencias
```python
# backend/app/repositories/salario_base_repository.py
# Reutilizada también en salario_plus_repository.py
def vigencias_solapan(existing_desde, existing_hasta, new_desde, new_hasta) -> bool
```
Regla: si `existing_hasta` es null → vigente indefinidamente → solapa con cualquier rango futuro.

### `AuditAction.LIQUIDACION_CERRAR`
Ya existía en `backend/app/core/audit_constants.py`. **No crear duplicado.**

---

## C-19 — Panel de Auditoría y Métricas

### Scope del COORDINADOR
El scope "propio" se resuelve en el **service**, nunca en la URL:
```python
# backend/app/services/metricas_auditoria_service.py
def resolver_actor_scope(perms: set[str], user_id: str) -> str | None:
    if "auditoria:ver" in perms: return None          # sin restricción
    if "auditoria:ver:propio" in perms: return user_id # solo sus datos
    return None
```
**Por qué**: exponer `actor_id` como parámetro URL permitiría que un COORDINADOR lo cambie y vea datos de otros. Violación de la regla de identidad desde la sesión.

### Queries de agregación
Usar **SQLAlchemy Core** (no ORM) para GROUP BY:
```python
select(func.date(AuditLog.fecha_hora), func.count(AuditLog.id)).group_by(...)
```
Los ORM mapped objects no representan bien resultados de GROUP BY.

### Estado de comunicaciones por docente
JOIN con tabla `comunicacion` (campo `estado` tipado e indexado), **NO** parsear el JSONB de `audit_log.detalle`. El JSONB es texto libre, no una fuente confiable para agregaciones.

### Límite configurable
```python
def aplicar_limite(limite: int | None, max_limit: int = 200) -> int:
    if not limite or limite <= 0: return max_limit
    return min(limite, max_limit)
```
- Cap silencioso: si `limite > 200` → retorna 200 sin error.
- Default y cap = 200 (constante de sistema, no configurable por tenant).

### Guard flexible OR de permisos
Para endpoints que aceptan `auditoria:ver` OR `auditoria:ver:propio`, usar `get_effective_permissions()` directamente en lugar de `require_permission()` (que solo acepta uno):
```python
perms = await get_effective_permissions(user_id=user.id, tenant_id=user.tenant_id, db=db)
if not perms & {"auditoria:ver", "auditoria:ver:propio"}:
    raise HTTPException(403)
```

---

## C-20 — Perfil y Mensajería Interna

### CUIL inmutable
El CUIL **no es editable por el usuario** (RN-25), pero sí por ADMIN directamente en DB.
La regla se impone en el service (no en constraint de DB) para mantener flexibilidad administrativa:
```python
def validar_campos_perfil(payload: dict) -> None:
    if "cuil" in payload:
        raise ValueError("cuil no es editable por el usuario")
```

### `modalidad_cobro` como string, no booleano
Campo `modalidad_cobro VARCHAR(20)` con valores `"liquidacion"` | `"factura"`.
- `FacturaService.crear()` de C-18 ya referenciaba este campo — C-20 lo hizo real en el modelo.
- Se agrega también `facturador BOOLEAN` como campo separado para F11.1.

### Mensajería interna — diseño de hilos
`hilo_id UUID` libre en `MensajeInterno` — **sin tabla Hilo separada**.
- El primer mensaje de un hilo genera el `hilo_id` (uuid4).
- El asunto del primer mensaje actúa como título del hilo.
- Si en el futuro se necesitan metadatos del hilo (participantes múltiples, título editable), se agrega tabla `Hilo` con una migración.

### Campos agregados a `Usuario`
Todos nullable para no romper registros existentes:
- `banco VARCHAR(255)`
- `regional VARCHAR(255)`
- `legajo_profesional VARCHAR(50)`
- `facturador BOOLEAN DEFAULT false`
- `modalidad_cobro VARCHAR(20) DEFAULT 'liquidacion'`

---

## Convenciones de arquitectura del backend

### Flujo obligatorio
```
Router → Service → Repository → Model
```
Nunca saltear capas. Nunca lógica de negocio en Routers. Nunca acceso directo a DB desde Services.

### Repositories
- Heredan de `TenantScopedRepository` — scoping por `tenant_id` automático.
- Queries de agregación (GROUP BY) van en un repo separado con SQLAlchemy Core.
- Guards de inmutabilidad van en el repository, no solo en el router.

### Schemas Pydantic
- Input (Create/Update): `extra='forbid'` — rechaza campos no declarados.
- Output (Out/Response): `from_attributes=True`.

### Routers
- Prefijo legacy (C-05 audit): `/api/admin/`
- Prefijo nuevo (C-18 en adelante): `/api/v1/<recurso>`
- Registrar en `app/main.py` con `application.include_router(xxx_router)`.

### Migraciones Alembic
- Nombre: `NNNN_descripcion_kebab.py`. Última: **0019**.
- Siempre escribir el `downgrade()`.
- Migraciones de datos (seed sin DDL): usar `op.get_bind()` + `sa.text()`.

### Modelos
- Tenant-scoped: heredar de `Base, TenantScopedModelMixin`.
- Global: heredar de `Base, BaseModelMixin`.
- PII cifrada: `EncryptedString()` — email, dni, cuil, cbu, alias_cbu.
- Soft delete: `mark_deleted()` del mixin. **Nunca hard delete**.
- Enums: `StrEnum` en Python, `String(N)` en DB.

---

## Patrones TDD del proyecto

### Regla principal
Las reglas de negocio se extraen como **funciones puras** (sin `self`, sin DB) para ser testeables sin fixtures. Ejemplos:
- `calcular_total()` — motor de liquidaciones
- `segmentar_liquidaciones()` — segmentación contable
- `vigencias_solapan()` — validación de grilla salarial
- `aplicar_limite()` — cap de métricas de auditoría
- `resolver_actor_scope()` — scope de COORDINADOR
- `validar_campos_perfil()` — regla de CUIL inmutable
- `validar_destinatario()` — regla de inbox (no mismo user)

### Tests de integración
Usan `pytest.skip("requires TEST_DATABASE_URL")` — **no mockear la DB** (regla dura del proyecto). Los tests se ejecutan en CI con DB real.

### Safety net
Antes de tocar código existente: `python -m pytest --tb=no -q` y capturar baseline.

### Estructura de archivos de test
```
test_<dominio>_c<NN>.py
  Group 1: unit puro (no DB)
  Group 2: unit puro (no DB)
  Group 3+: integration (require TEST_DATABASE_URL → skip en local)
```

---

## Permisos RBAC — catálogo

| Permiso | Roles que lo tienen | Módulo |
|---------|--------------------|----|
| `estructura:gestionar` | ADMIN | Carreras, cohortes, materias |
| `atrasados:ver` | TUTOR, PROFESOR, COORDINADOR, ADMIN | Monitor de atrasados |
| `auditoria:ver` | ADMIN, COORDINADOR, FINANZAS | Panel auditoría completo |
| `auditoria:ver:propio` | COORDINADOR | Solo sus propias acciones |
| `liquidaciones:ver` | FINANZAS, ADMIN | Ver liquidaciones |
| `liquidaciones:cerrar` | FINANZAS | Cerrar período |
| `liquidaciones:configurar-salarios` | FINANZAS | ABM grilla salarial |
| `facturas:ver` | FINANZAS | Ver facturas |
| `facturas:gestionar` | FINANZAS | Crear y gestionar facturas |

---

## Gotchas y advertencias

1. **Rama sin ancestro común** — `azul2` no tiene ancestro común con `main`. No hacer `git merge` directo. Traer como rama independiente con `git checkout -b azul2 origin/Azul2`.

2. **307+ tests skipped en local** — los tests de integración se saltan porque `TEST_DATABASE_URL` no está configurada. No es un error — se ejecutan en CI con DB real.

3. **`openspec new change` requiere lowercase** — falla con error explícito si pasás `C-18-...`. Usar `c-18-...`.

4. **`FacturaService` y `modalidad_cobro`** — el servicio de facturas (C-18) ya referenciaba `usuario.modalidad_cobro`, pero el campo no existía en el modelo `Usuario` hasta C-20. Si corrés la suite de integración entre C-18 y C-20 sin haber aplicado la migración 0019, el test de `crear()` falla.

5. **Prefijo de routers inconsistente** — el router de auditoría legacy usa `/api/admin/audit-log`. Los nuevos routers (C-18+) usan `/api/v1/`. No unificar sin decisión explícita del equipo.

6. **`AuditAction.LIQUIDACION_CERRAR`** ya existe en `audit_constants.py`. No crear duplicado.

7. **`mv` no funciona en Windows para mover directorios en bash** — usar `python -c "import shutil; shutil.move(src, dst)"`.

---

## Mapa de migraciones

| # | Descripción |
|---|-------------|
| 0001–0006 | Infraestructura, auth, RBAC, audit, estructura académica, usuarios |
| 0007 | Padrón (VersionPadron, EntradaPadron) |
| 0008 | Calificaciones y umbral |
| 0009 | Seed permisos atrasados |
| 0010–0015 | Comunicaciones, encuentros, evaluaciones, avisos, tareas, programas |
| **0016** | **C-18** — salario_base, salario_plus, liquidacion, factura + ALTER materia/tenant |
| **0017** | **C-18** — seed permisos liquidaciones y facturas para FINANZAS |
| **0018** | **C-19** — seed `auditoria:ver` para FINANZAS |
| **0019** | **C-20** — ALTER usuario (banco/regional/legajo_profesional/facturador/modalidad_cobro) + CREATE mensaje_interno |

---

*Última actualización: 2026-06-06 — tras completar C-18, C-19, C-20.*
