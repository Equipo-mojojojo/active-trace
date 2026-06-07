## Why

El sistema actual carece de un módulo de liquidaciones y honorarios, lo que obliga al equipo de FINANZAS a calcular manualmente —fuera del sistema— los pagos a docentes cada período. Sin grilla salarial ni cálculo automático, se pierde trazabilidad, se incrementa el riesgo de error y se dificulta la auditoría.

C-18 entrega el módulo completo de liquidaciones sobre la estructura académica (C-06) y de usuarios (C-07) ya existente, permitiendo a FINANZAS: configurar salarios, calcular liquidaciones por cohorte×mes, cerrar períodos (inmutable), gestionar facturas de docentes independientes y obtener KPIs contables separados.

## What Changes

- **4 modelos ORM nuevos** con `TenantScopedModelMixin`:
  - `SalarioBase` — monto base por rol (PROFESOR/TUTOR/NEXO/COORDINADOR) con vigencia temporal
  - `SalarioPlus` — plus por grupo de materia × rol con vigencia temporal
  - `Liquidacion` — liquidación mensual individual por docente (Base + Plus = Total), estados Abierta/Cerrada
  - `Factura` — factura de docentes que facturan (Pendiente/Abonada)
- **Enums de dominio**: `EstadoLiquidacion` (Abierta/Cerrada), `EstadoFactura` (Pendiente/Abonada), `RolLiquidacion` → reusa `RolDocente` existente
- **Nuevos permisos modulares**: `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `liquidaciones:exportar`, `facturas:gestionar`
- **API REST**:
  - `/api/liquidaciones/*` — ABM de grilla salarial, cálculo, cierre, historial
  - `/api/facturas/*` — ABM de facturas de docentes facturantes
- **Cálculo automático**: `Total = Base(rol, vigente al mes) + Σ(Plus(grupo, rol) × N comisiones activas)` según RN-21/RN-34
- **Auditoría**: evento `LIQUIDACION_CERRAR` al cerrar una liquidación (inmutable)
- **Migración Alembic** incremental para las 4 tablas
- **Tests**: CRUD, cálculo, cierre inmutable, aislamiento multi-tenant, reglas de grilla salarial

## Capabilities

### New Capabilities
- `liquidaciones-salarios`: Gestión de grilla salarial — ABM de SalarioBase y SalarioPlus con control de vigencia y solapamiento (RN-31/32/33)
- `liquidaciones-calculo`: Cálculo y cierre de liquidaciones mensuales por (cohorte×mes), inmutabilidad al cerrar (RN-21/22/34/37)
- `facturas-docentes`: Gestión de facturas de docentes facturantes — carga, adjunto, estados Pendiente/Abonada, exclusión de liquidación general (RN-35/39/40)

### Modified Capabilities
<!-- Sin cambios en capacidades existentes — este change crea el módulo de liquidaciones desde cero sobre las entidades existentes de estructura académica y usuarios. -->

## Impact

- **Backend**: 4 modelos nuevos + repositorios + schemas + servicios + routers
- **Base de datos**: Una migración que crea las tablas `salario_base`, `salario_plus`, `liquidacion`, `factura` con sus FK, constraints y defaults
- **Permisos**: 5 permisos nuevos (`liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `liquidaciones:exportar`, `facturas:gestionar`) que deben seedearse y asignarse al rol FINANZAS por defecto
- **Auditoría**: Nuevo código de acción `LIQUIDACION_CERRAR`
- **Dependencias**: Requiere C-07 (Usuario, Asignacion) y C-06 (Carrera, Cohorte, Materia) ya completados
- **Multi-tenancy**: Toda entidad lleva `tenant_id`; filtros automáticos vía `TenantScopedRepository`
- **Frontend**: Eventualmente requerirá vistas FINANZAS para gestión de grilla, liquidaciones y facturas (change futuro)
