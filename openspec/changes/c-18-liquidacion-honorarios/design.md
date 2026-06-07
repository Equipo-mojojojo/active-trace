## Context

Activia-trace ya cuenta con la infraestructura base (C-01), multi-tenancy (C-02), auth (C-03), RBAC (C-04), auditoría (C-05), estructura académica (C-06) y usuarios/asignaciones (C-07). Sobre esa base, C-18 introduce el **módulo de liquidaciones y honorarios** — el componente financiero que permite a FINANZAS calcular y cerrar pagos a docentes.

El módulo opera sobre 5 entidades nuevas — GrupoMateria, SalarioBase, SalarioPlus, Liquidacion, Factura — e integra con los modelos existentes de Usuario, Asignacion, Cohorte y Materia. El cálculo sigue la fórmula `Total = Base(rol) + Σ(Plus(grupo×rol)×comisiones)` con vigencia temporal y cierre inmutable.

**Stakeholders**: FINANZAS (usuario principal), ADMIN (configuración), docentes (consulta pasiva vía frontend futuro).

**Governance**: CRÍTICO — maneja datos financieros, requiere precisión matemática y control de acceso fino.

## Goals / Non-Goals

**Goals:**

- Implementar modelos ORM para SalarioBase, SalarioPlus, Liquidacion y Factura usando `TenantScopedModelMixin`
- ABM completo de grilla salarial (SalarioBase + SalarioPlus) con control de vigencia y detección de solapamientos (RN-31/32/33)
- Cálculo automático de liquidación por (cohorte × mes) para cada docente activo: Base + Σ(Plus) = Total (RN-21/34)
- Cierre de liquidación con inmutabilidad total (RN-22/37)
- Gestión de facturas para docentes facturantes con exclusión de liquidación general (RN-35/39/40)
- KPIs contables separados: total sin factura vs. total con factura (RN-36/38)
- Auditoría: evento `LIQUIDACION_CERRAR` al cerrar
- Nuevos permisos modulares: `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `liquidaciones:exportar`, `facturas:gestionar`
- Tests con base real que cubran cálculo, cierre, unicidad, aislamiento multi-tenant y reglas de grilla

**Non-Goals:**

- No incluye frontend ni vistas de UI — solo backend API
- No incluye exportación a formatos contables externos (la exportación se limita a structured JSON/CSV)
- No incluye integración con sistemas bancarios para pagos automáticos
- No incluye workflow de aprobación multi-paso para el cierre (el cierre lo ejecuta FINANZAS directamente)
- No incluye notificaciones automáticas a docentes al cerrar liquidación
- No incluye histórico de cambios en la grilla salarial (el versionado por vigencia ya lo provee el modelo temporal)

## Entidades y Relaciones

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               Tenant                                         │
└────┬──────────┬──────────┬──────────┬─────────────┬─────────────────────────┘
     │          │          │          │             │
     ▼          ▼          ▼          ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ Grupo   │ │Salario  │ │ Salario │ │Liquida- │ │   Factura    │
│Materia  │ │ Base    │ │  Plus   │ │  ción   │ │              │
├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├──────────────┤
│id (PK)  │ │id (PK)  │ │id (PK)  │ │id (PK)  │ │id (PK)       │
│tenant_id│ │tenant_id│ │tenant_id│ │tenant_id│ │tenant_id     │
│clave    │ │rol      │ │grupo_id │ │cohorte  │ │usuario_id    │
│descrip- │ │monto    │ │(FK→Gpo) │ │periodo  │ │periodo       │
│ción     │ │desde    │ │rol      │ │usuario  │ │detalle       │
│         │ │hasta    │ │descrip- │ │rol      │ │ref_archivo   │
│         │ │         │ │ción     │ │comision │ │tamano_kb     │
│         │ │         │ │monto    │ │monto_ba │ │estado        │
│         │ │         │ │desde    │ │se       │ │cargada_at    │
│         │ │         │ │hasta    │ │monto_pl │ │abonada_at    │
│         │ │         │ │         │ │us       │ │              │
│         │ │         │ │         │ │total    │ │              │
│         │ │         │ │         │ │es_nexo  │ │              │
│         │ │         │ │         │ │excluido │ │              │
│         │ │         │ │         │ │_factura │ │              │
│         │ │         │ │         │ │estado   │ │              │
│         │ │         │ │         │ │(Abierta │ │              │
│         │ │         │ │         │ │/Cerrada)│ │              │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────────┘

Relaciones adicionales con Materia (modelo existente):
  Materia.grupo_materia_id → GrupoMateria.id (FK nullable — cada materia se asigna a un grupo)

FKs:
  SalarioBase.tenant_id    → Tenant.id
  SalarioPlus.tenant_id    → Tenant.id
  SalarioPlus.grupo_id     → GrupoMateria.id  (FK al catálogo de grupos)
  Liquidacion.tenant_id    → Tenant.id
  Liquidacion.cohorte_id   → Cohorte.id
  Liquidacion.usuario_id   → Usuario.id
  Factura.tenant_id        → Tenant.id
  Factura.usuario_id       → Usuario.id (con facturador = true)

Claves únicas:
  GrupoMateria:      UNIQUE(tenant_id, clave)  — cada clave es única por tenant
  SalarioBase:       UNIQUE(tenant_id, rol, desde)  — un valor base por rol por fecha de inicio
  SalarioPlus:       UNIQUE(tenant_id, grupo_id, rol, desde) — un plus por grupo×rol por fecha
  Liquidacion:       UNIQUE(tenant_id, cohorte_id, periodo, usuario_id) — una liquidación por docente×período×cohorte
```

### Decisiones de naming

| Elemento | Decisión | Motivo |
|----------|----------|--------|
| `rol` en SalarioBase/Plus | String (reusa `RolDocente` existente: PROFESOR/TUTOR/NEXO/COORDINADOR) | Coincide con el enum del modelo Asignacion; no se define un enum nuevo |
| `grupo_id` en SalarioPlus | FK → GrupoMateria.id | PA-22: catálogo de grupos dedicado. El ADMIN define las claves (PROG, BD, ING, etc.) en GrupoMateria y asigna cada materia a un grupo |
| `es_nexo` en Liquidacion | Booleano desnormalizado | Facilita la separación contable RN-36 sin tener que cruzar Asignacion cada vez que se lista |
| `excluido_por_factura` | Booleano derivado de `Usuario.facturador` al momento del cálculo | RN-35: se calcula al generar la liquidación; si después el usuario cambia su modalidad, las liquidaciones ya cerradas no se ven afectadas |
| `grupo_materia` | Tabla catálogo con `clave` y `descripcion` por tenant | PA-22: cada tenant define sus propios grupos. La FK `Materia.grupo_materia_id` asigna una materia a su grupo |
| `periodo` | Texto en formato `AAAA-MM` | Simple, legible, ordenable lexicográficamente |

## Enums de dominio (nuevos en `app/models/enums.py`)

```python
class EstadoLiquidacion(StrEnum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"

class EstadoFactura(StrEnum):
    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"
```

Se reusa `RolDocente` del modelo Asignacion (PROFESOR, TUTOR, NEXO, COORDINADOR). No se crea un enum redundante.

## Decisions

### D1 — Cálculo de liquidación: service layer con consultas a repositorios, no store procedure

**Decisión**: El cálculo de liquidaciones se implementa en `LiquidacionService.calcular(cohorte_id, periodo)` usando consultas Python + SQLAlchemy. No se usa un store procedure ni funciones PG.

**Alternativa considerada**: Función PL/pgSQL que calcule todo en una sola query.

**Razón**: El cálculo requiere lógica de negocio (determinar Plus aplicables según grupo de materia, filtrar facturantes, calcular nexos por separado) que es más mantenible en Python. La performance no es crítica para el volumen esperado (decenas a cientos de docentes por tenant, no miles). Si en el futuro escala, se puede optimizar a una query SQL única dentro del service.

### D2 — Inmutabilidad por flag + constraint unique, no por tabla de historial

**Decisión**: La inmutabilidad de liquidaciones cerradas se implementa con un flag `estado = Cerrada` y una validación en service que rechaza updates si el estado ya es Cerrada. No se mueven registros a una tabla de historial.

**Alternativa considerada**: Mover registros a `liquidacion_historica` al cerrar.

**Razón**: La inmutabilidad es una regla de negocio, no de performance. Mantener los datos en la misma tabla simplifica consultas de historial (F10.3) y reportes. El flag permite auditoría y es consistente con el patrón de soft delete del proyecto.

### D3 — Plus como registro único por grupo×rol, no por materia individual

**Decisión**: SalarioPlus se define por (grupo, rol), no hay un plus individual por materia. El algoritmo calcula cuántas comisiones activas del docente caen en cada grupo y acumula N × monto_del_plus.

**Alternativa considerada**: Un plus por materia concreta.

**Razón**: Es más granular que la KB (RN-33 dice "por categoría de materia"). La KB ya modela `SalarioPlus.grupo` como categoría; RN-33 permite acumulación múltiple. El algoritmo es: `Σ(grupo → contar comisiones del docente en ese grupo → monto_plus × count)`.

### D4 — Liquidación se calcula a pedido (on-demand), no programada

**Decisión**: El cálculo de liquidación se ejecuta cuando FINANZAS lo solicita explícitamente (POST /api/liquidaciones/calcular). No hay un job programado (cron) que lo ejecute automáticamente.

**Alternativa considerada**: Cálculo automático al inicio de cada mes vía worker.

**Razón**: FINANZAS necesita control sobre cuándo se genera la liquidación (puede haber ajustes de grilla pendientes, docentes sin asignar, etc.). El cálculo on-demand da ese control. Un cálculo automático podría generar liquidaciones incorrectas si la grilla no está actualizada.

### D5 — Soft delete en SalarioBase y SalarioPlus, NO en Liquidacion y Factura

**Decisión**: SalarioBase y SalarioPlus heredan `TenantScopedModelMixin` (soft delete). Liquidacion y Factura solo heredan `UUIDPrimaryKeyMixin` + `TimestampMixin` + `TenantIdMixin` (sin soft delete).

**Alternativa considerada**: Soft delete en todas.

**Razón**: Liquidaciones y facturas son registros financieros inmutables que nunca deben eliminarse ni siquiera lógicamente. El soft delete podría ocultar registros de auditoría financiera. En cambio, la grilla salarial puede tener entradas obsoletas/erróneas que convenga ocultar pero no destruir.

### D6 — Catálogo de grupos de materias (PA-22, resuelta ✅)

**Decisión**: Se implementa **Opción A — tabla `grupo_materia` dedicada** por tenant.

El tenant ADMIN define un catálogo de grupos (ej: `PROG`, `BD`, `ING`, `MAT`, etc.) en la entidad `GrupoMateria`. Cada materia del catálogo existente (`Materia`) se asigna a un grupo mediante `Materia.grupo_materia_id` (FK nullable — una materia puede no tener grupo asignado).

`SalarioPlus.grupo_id` es FK a `GrupoMateria.id`, no texto libre. Esto garantiza consistencia referencial en el cálculo de liquidaciones.

**Impacto en el modelo**:
- Nueva entidad: `GrupoMateria { id, tenant_id, clave, descripcion }` con UNIQUE `(tenant_id, clave)`
- FK nullable `Materia.grupo_materia_id → GrupoMateria.id` (modifica modelo existente)
- `SalarioPlus.grupo` se reemplaza por `SalarioPlus.grupo_id → GrupoMateria.id`
- Tenant ADMIN gestiona alta/baja de grupos mediante un CRUD que se agrega al módulo admin existente (se agrega como tarea separada)

### D7 — Acumulación de Plus entre comisiones del mismo grupo (PA-23, resuelta ✅)

**Decisión**: Se implementa **Opción A — Acumular** (RN-33 literal).

Si un docente da 3 comisiones de materias bajo el grupo `PROG`, y existe `SalarioPlus(grupo_id=X, rol=PROFESOR, monto=500)`, el plus total es `500 × 3 = 1500`.

El algoritmo de cálculo:
```
plus_total = Σ(por cada grupo → monto_plus[grupo_id][rol] × cantidad_comisiones_docente_en_grupo)
```

El contador de comisiones se obtiene agrupando las asignaciones activas del docente en el período por `Materia.grupo_materia_id`.

## Cálculo — Algoritmo

```
función calcular_liquidacion(cohorte_id, periodo):
    1. Obtener grilla_base vigente para el período (SalarioBase con desde <= periodo <= hasta)
    2. Obtener grilla_plus vigente para el período (SalarioPlus con desde <= periodo <= hasta)
    3. Obtener asignaciones activas de la cohorte (Asignacion con cohorte_id, vigentes en el período)
    4. Por cada usuario con asignaciones activas:
        a. Si usuario.facturador = true → calcular Liquidacion con excluido_por_factura = true,
           pero incluir en KPIs informativos
        b. Determinar rol (único por liquidación; si tiene múltiples roles, se liquida por separado)
        c. monto_base = SalarioBase[rol].monto
        d. Por cada asignación activa:
            i. grupo_id = Materia.grupo_materia_id (FK a GrupoMateria)
            ii. monto_plus += SalarioPlus[grupo_id][rol].monto (RN-34: acumula por comisión)
        e. total = monto_base + monto_plus
        f. es_nexo = (rol == NEXO)
        g. Crear/Actualizar Liquidacion en estado Abierta
```

## Endpoints REST

### `/api/liquidaciones/salarios-base`

| Método | Ruta | Descripción | Códigos | Permiso |
|--------|------|-------------|---------|---------|
| GET | `/api/liquidaciones/salarios-base` | Listar salarios base del tenant (vigentes o por filtro) | 200 | `liquidaciones:configurar-salarios` |
| GET | `/api/liquidaciones/salarios-base/{id}` | Obtener salario base por ID | 200, 404 | `liquidaciones:configurar-salarios` |
| POST | `/api/liquidaciones/salarios-base` | Crear salario base | 201, 409, 422 | `liquidaciones:configurar-salarios` |
| PUT | `/api/liquidaciones/salarios-base/{id}` | Actualizar salario base | 200, 404, 409 | `liquidaciones:configurar-salarios` |
| DELETE | `/api/liquidaciones/salarios-base/{id}` | Soft delete salario base | 204, 404 | `liquidaciones:configurar-salarios` |

**422** = solapamiento de vigencia con registro existente del mismo rol.

### `/api/liquidaciones/salarios-plus`

| Método | Ruta | Descripción | Códigos | Permiso |
|--------|------|-------------|---------|---------|
| GET | `/api/liquidaciones/salarios-plus` | Listar plus del tenant | 200 | `liquidaciones:configurar-salarios` |
| GET | `/api/liquidaciones/salarios-plus/{id}` | Obtener plus por ID | 200, 404 | `liquidaciones:configurar-salarios` |
| POST | `/api/liquidaciones/salarios-plus` | Crear plus | 201, 409, 422 | `liquidaciones:configurar-salarios` |
| PUT | `/api/liquidaciones/salarios-plus/{id}` | Actualizar plus | 200, 404, 409 | `liquidaciones:configurar-salarios` |
| DELETE | `/api/liquidaciones/salarios-plus/{id}` | Soft delete plus | 204, 404 | `liquidaciones:configurar-salarios` |

**422** = solapamiento de vigencia con registro existente del mismo (grupo, rol).

### `/api/liquidaciones/calculo`

| Método | Ruta | Descripción | Códigos | Permiso |
|--------|------|-------------|---------|---------|
| POST | `/api/liquidaciones/calcular` | Calcula (o recalcula) liquidaciones del período para una cohorte | 200, 422 | `liquidaciones:ver` |
| GET | `/api/liquidaciones` | Listar liquidaciones del tenant (filtros: cohorte, periodo, usuario, estado) | 200 | `liquidaciones:ver` |
| GET | `/api/liquidaciones/{id}` | Obtener liquidación por ID con detalle | 200, 404 | `liquidaciones:ver` |
| POST | `/api/liquidaciones/{id}/cerrar` | Cerrar liquidación (inmutable) | 200, 404, 409 | `liquidaciones:cerrar` |
| GET | `/api/liquidaciones/kpis` | KPIs contables del período (totales con/sin factura, separación NEXO) | 200 | `liquidaciones:ver` |
| GET | `/api/liquidaciones/historial` | Historial de liquidaciones cerradas | 200 | `liquidaciones:ver` |

**422** en POST `/calcular` = cohorte no existe o período inválido.
**409** en POST `/{id}/cerrar` = liquidación ya está cerrada.

### `/api/facturas`

| Método | Ruta | Descripción | Códigos | Permiso |
|--------|------|-------------|---------|---------|
| GET | `/api/facturas` | Listar facturas del tenant (filtros: usuario, periodo, estado) | 200 | `facturas:gestionar` |
| GET | `/api/facturas/{id}` | Obtener factura por ID | 200, 404 | `facturas:gestionar` |
| POST | `/api/facturas` | Crear factura (carga de datos + archivo) | 201, 422 | `facturas:gestionar` |
| PUT | `/api/facturas/{id}` | Actualizar factura (solo si está Pendiente) | 200, 404, 409 | `facturas:gestionar` |
| DELETE | `/api/facturas/{id}` | Hard delete NO — soft delete NO — las facturas no se eliminan (son registros financieros) | — | — |
| POST | `/api/facturas/{id}/abonar` | Marcar factura como abonada | 200, 404, 409 | `facturas:gestionar` |

**409** en POST `/{id}/abonar` = factura ya está abonada.
Las facturas no tienen DELETE (D5 — registros financieros inmutables).

### Permisos

| Permiso | Módulo | Acción | Roles asignados (seed) |
|---------|--------|--------|----------------------|
| `liquidaciones:ver` | liquidaciones | ver | FINANZAS, ADMIN |
| `liquidaciones:cerrar` | liquidaciones | cerrar | FINANZAS |
| `liquidaciones:configurar-salarios` | liquidaciones | configurar-salarios | FINANZAS |
| `liquidaciones:exportar` | liquidaciones | exportar | FINANZAS |
| `facturas:gestionar` | facturas | gestionar | FINANZAS |

### Parámetros de request/response

Todos los schemas Pydantic v2 siguen `ConfigDict(extra="forbid")` en Create/Update y `ConfigDict(from_attributes=True)` en Response.

Ejemplo:
```python
class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rol: RolDocente
    monto: Decimal
    desde: date
    hasta: date | None = None

class LiquidacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cohorte_id: UUID
    periodo: str
    usuario_id: UUID
    rol: RolDocente
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: EstadoLiquidacion
```

## Migration Plan

### Creación

```bash
cd backend
alembic revision -m "create liquidaciones y honorarios" --rev-id <next>
```

La migración debe:
1. Crear tabla `grupo_materia` con FK a `tenant(id)`, UNIQUE `(tenant_id, clave)`
2. Agregar FK nullable `Materia.grupo_materia_id → GrupoMateria.id` (ALTER TABLE al modelo existente)
3. Crear tabla `salario_base` con FK a `tenant(id)`, UNIQUE `(tenant_id, rol, desde)`
4. Crear tabla `salario_plus` con FK a `tenant(id)`, FK a `grupo_materia(id)`, UNIQUE `(tenant_id, grupo_id, rol, desde)`
5. Crear tabla `liquidacion` con FK a `tenant(id)`, FK a `cohorte(id)`, FK a `usuario(id)`, UNIQUE `(tenant_id, cohorte_id, periodo, usuario_id)`
6. Crear tabla `factura` con FK a `tenant(id)`, FK a `usuario(id)`

### Rollback

`alembic downgrade <prev>` elimina las tablas en orden inverso (factura → liquidacion → salario_plus → salario_base → grupo_materia) y revierte el ALTER TABLE de Materia.

### Seed de permisos

Los 5 permisos nuevos deben agregarse a la seed y asignarse al rol FINANZAS (y `liquidaciones:ver` también a ADMIN).

## Riesgos / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Datos incompletos**: una materia sin `grupo_materia_id` asignado no genera plus en la liquidación. | Validar en el cálculo que todas las materias con asignaciones activas tengan grupo asignado; emitir warning por cada materia sin grupo. |
| **Precisión decimal**: usar `Float` en montos puede causar errores de redondeo. | Usar `DECIMAL(10,2)` (o `Numeric(10,2)` en SQLAlchemy) para todos los campos monetarios. Pydantic v2 usa `Decimal` que preserva precisión. |
| **Liquidaciones duplicadas**: si FINANZAS ejecuta POST /calcular dos veces, se crean duplicados. | El UNIQUE constraint `(tenant_id, cohorte_id, periodo, usuario_id)` en Liquidacion lo impide a nivel BD. El service debe hacer upsert (UPDATE si existe, INSERT si no). |
| **Cierre concurrente**: dos requests de cierre simultáneas sobre la misma liquidación. | Usar `select_for_update` al leer la liquidación antes de cerrar para obtener lock pesimista. Alternativa: manejar el 409 si el estado ya es Cerrada. |
| **Multi-tenancy**: un error en el filtro de tenant podría exponer datos financieros de otra institución. | Usar `TenantScopedRepository` que filtra por `tenant_id` en toda operación. Los endpoints inyectan `tenant_id` desde la sesión autenticada. |
| **Volumen de datos**: al calcular la liquidación de una cohorte completa, se generan N registros Liquidacion. Si hay 200 docentes, son 200 inserts. | No es un volumen problemático. Si crece, se puede optimizar con `bulk_insert`. |

## Open Questions

1. **Rol en Liquidacion**: ¿Una liquidación puede tener múltiples roles (ej: un usuario que es PROFESOR y TUTOR a la vez)? La KB sugiere que sí hay asignaciones múltiples. Decisión tentativa: una Liquidacion por rol. Si un usuario tiene 2 roles, recibe 2 liquidaciones separadas en el mismo período.
2. **Archivo adjunto en Factura**: ¿Se almacena en disco local, S3, o servicio de almacenamiento externo? Decisión: usar `referencia_archivo` (misma estrategia que ProgramaMateria) — el cómo se resuelve en un change de infraestructura futuro.
3. **CRUD de GrupoMateria**: ¿Dónde se aloja? ¿En un endpoint admin separado o como parte del módulo de liquidaciones? Decisión tentativa: incluir endpoints CRUD simples `/api/admin/grupos-materia` como parte de este change para que el tenant ADMIN pueda configurar los grupos antes de usarlos en la grilla.
