/**
 * TypeScript types derived from backend contracts for the finanzas feature.
 *
 * Sources:
 *  - liquidacion-calculo spec (C-18): GET /api/liquidaciones/
 *  - grilla-salarial spec (C-18): /api/liquidaciones/salarios/base, /api/liquidaciones/salarios/plus
 *  - factura-docente spec (C-18): /api/facturas/
 */

// ─── Roles ────────────────────────────────────────────────────────────────────

export type RolDocente = 'PROFESOR' | 'TUTOR' | 'COORDINADOR' | 'NEXO' | 'ADMIN' | 'FINANZAS'

// ─── Liquidaciones ────────────────────────────────────────────────────────────

export interface DocenteEnLiquidacion {
  usuario_id: string
  nombre: string
  rol: RolDocente
  comisiones: number
  salario_base: number
  plus: number
  total: number
}

export interface LiquidacionResponse {
  periodo: string
  cerrada: boolean
  total_sin_factura: number
  total_con_factura: number
  general: DocenteEnLiquidacion[]
  nexo: DocenteEnLiquidacion[]
  facturantes: DocenteEnLiquidacion[]
}

export interface LiquidacionHistorialItem {
  periodo: string
  cerrada_en: string
  total_sin_factura: number
  total_con_factura: number
}

export interface LiquidacionFilters {
  periodo: string
  usuario_id?: string
  cohorte_id?: string
}

// ─── Grilla Salarial ──────────────────────────────────────────────────────────

export interface SalarioBase {
  id: string
  rol: RolDocente
  monto: number
  vigencia_desde: string
  vigencia_hasta: string | null
}

export interface SalarioBaseCreate {
  rol: RolDocente
  monto: number
  vigencia_desde: string
  vigencia_hasta?: string
}

export interface SalarioPlus {
  id: string
  clave: string
  rol: RolDocente
  descripcion: string
  monto: number
  vigencia_desde: string
  vigencia_hasta: string | null
}

export interface SalarioPlusCreate {
  clave: string
  rol: RolDocente
  descripcion: string
  monto: number
  vigencia_desde: string
  vigencia_hasta?: string
}

export interface SalarioPlusFilters {
  clave?: string
  rol?: string
}

// ─── Facturas ─────────────────────────────────────────────────────────────────

export type EstadoFactura = 'pendiente' | 'abonada'

export interface Factura {
  id: string
  usuario_id: string
  nombre_docente: string
  periodo: string
  detalle: string
  monto: number
  fecha_carga: string
  estado: EstadoFactura
  archivo_path: string | null
}

export interface FacturaCreate {
  usuario_id: string
  periodo: string
  monto: number
  detalle: string
  fecha_carga: string
}

export interface FacturaFilters {
  usuario_id?: string
  estado?: EstadoFactura
  fecha_desde?: string
  fecha_hasta?: string
  q?: string
}
