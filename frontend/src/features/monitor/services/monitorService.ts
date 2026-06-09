/**
 * Service for monitor de seguimiento (F2.8).
 *
 * Endpoints:
 *  GET /api/v1/analisis/monitor — F2.7-F2.9 (filterable)
 */
import { api } from '@/shared/services/api'
import type { MonitorFiltros, MonitorResponse } from '@/features/profesor/types/profesor.types'

export const monitorService = {
  async getMonitor(filtros: MonitorFiltros = {}): Promise<MonitorResponse> {
    const params: Record<string, unknown> = {}

    if (filtros.materia_id) params['materia_id'] = filtros.materia_id
    if (filtros.comision) params['comision'] = filtros.comision
    if (filtros.regional) params['regional'] = filtros.regional
    if (filtros.q) params['q'] = filtros.q
    if (filtros.min_aprobadas !== undefined) params['min_aprobadas'] = filtros.min_aprobadas
    params['limit'] = filtros.limit ?? 1000
    params['offset'] = filtros.offset ?? 0

    const { data } = await api.get<MonitorResponse>('/analisis/monitor', { params })
    return data
  },
}
