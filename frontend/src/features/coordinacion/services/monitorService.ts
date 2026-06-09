/**
 * Service for monitor coordinacion (F2.9) API calls.
 *
 * Endpoint (backend/app/api/v1/routers/analisis.py):
 *  GET /api/v1/analisis/monitor — F2.7–F2.9 (atrasados:ver)
 *
 * Note: The monitor endpoint is shared between PROFESOR (F2.7/F2.8) and
 * COORDINADOR (F2.9). The COORDINADOR uses it without materia_id filter
 * to get the full institutional view, plus fecha_desde/fecha_hasta filters.
 */
import { api } from '@/shared/services/api'
import type { MonitorCoordResponse, MonitorFilters } from '../types/coordinacion.types'

export const monitorService = {
  async getMonitorCoord(filters: MonitorFilters = {}): Promise<MonitorCoordResponse> {
    const params: Record<string, string | number | undefined> = {}

    if (filters.materia_id) params.materia_id = filters.materia_id
    if (filters.comision) params.comision = filters.comision
    if (filters.regional) params.regional = filters.regional
    if (filters.q) params.q = filters.q
    if (filters.fecha_desde) params.fecha_desde = filters.fecha_desde
    if (filters.fecha_hasta) params.fecha_hasta = filters.fecha_hasta
    if (filters.carrera_id) params.carrera_id = filters.carrera_id
    if (filters.docente) params.docente = filters.docente
    if (filters.estado && filters.estado !== 'todos') params.estado = filters.estado
    if (filters.limit) params.limit = filters.limit
    if (filters.offset) params.offset = filters.offset

    const { data } = await api.get<MonitorCoordResponse>('/analisis/monitor', { params })
    return data
  },
}
