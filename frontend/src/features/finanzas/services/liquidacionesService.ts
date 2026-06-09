/**
 * Service for liquidaciones API calls.
 *
 * Endpoints (backend spec liquidacion-calculo, C-18):
 *  GET  /api/liquidaciones/              — Get liquidación del período
 *  POST /api/liquidaciones/{periodo}/cerrar — Cerrar liquidación
 *  GET  /api/liquidaciones/historial     — Historial de períodos cerrados
 *  GET  /api/liquidaciones/exportar      — Exportar liquidación (blob)
 */
import { api } from '@/shared/services/api'
import type {
  LiquidacionResponse,
  LiquidacionHistorialItem,
  LiquidacionFilters,
} from '../types/finanzas.types'

export const liquidacionesService = {
  async getLiquidaciones(filters: LiquidacionFilters): Promise<LiquidacionResponse> {
    const { data } = await api.get<LiquidacionResponse>('/api/liquidaciones/', {
      params: filters,
    })
    return data
  },

  async cerrarLiquidacion(periodo: string): Promise<LiquidacionResponse> {
    const { data } = await api.post<LiquidacionResponse>(
      `/api/liquidaciones/${periodo}/cerrar`,
    )
    return data
  },

  async getHistorial(periodo?: string): Promise<LiquidacionHistorialItem[]> {
    const { data } = await api.get<LiquidacionHistorialItem[]>(
      '/api/liquidaciones/historial',
      { params: periodo ? { periodo } : undefined },
    )
    return data
  },

  async exportarLiquidacion(filters: LiquidacionFilters): Promise<Blob> {
    const { data } = await api.get<Blob>('/api/liquidaciones/exportar', {
      params: filters,
      responseType: 'blob',
    })
    return data
  },
}
