/**
 * Service for equipos docentes API calls.
 *
 * Endpoints (backend/app/api/v1/routers/equipos.py):
 *  GET  /api/equipos/asignaciones          — All tenant assignments (equipos:asignar)
 *  POST /api/equipos/asignaciones/masiva   — Bulk assignment
 *  POST /api/equipos/clonar               — Clone team between cohortes
 *  GET  /api/equipos/export               — CSV export
 *
 * Endpoints (backend/app/api/v1/routers/asignaciones.py):
 *  POST   /api/asignaciones               — Create assignment
 *  PATCH  /api/asignaciones/{id}          — Update assignment
 *  DELETE /api/asignaciones/{id}          — Soft delete assignment
 */
import { api } from '@/shared/services/api'
import type {
  Asignacion,
  AsignacionCreate,
  AsignacionMasivaRequest,
  AsignacionMasivaResponse,
  ClonarEquipoRequest,
  ClonarEquipoResponse,
  EquiposFilters,
} from '../types/coordinacion.types'

export const equiposService = {
  async getEquipos(filters: EquiposFilters = {}): Promise<Asignacion[]> {
    const { data } = await api.get<Asignacion[]>('/api/equipos/asignaciones', {
      params: filters,
    })
    return data
  },

  async createAsignacion(payload: AsignacionCreate): Promise<Asignacion> {
    const { data } = await api.post<Asignacion>('/api/asignaciones', payload)
    return data
  },

  async updateAsignacion(id: string, payload: Partial<AsignacionCreate>): Promise<Asignacion> {
    const { data } = await api.patch<Asignacion>(`/api/asignaciones/${id}`, payload)
    return data
  },

  async deleteAsignacion(id: string): Promise<void> {
    await api.delete(`/api/asignaciones/${id}`)
  },

  async asignacionMasiva(payload: AsignacionMasivaRequest): Promise<AsignacionMasivaResponse> {
    const { data } = await api.post<AsignacionMasivaResponse>(
      '/api/equipos/asignaciones/masiva',
      payload,
    )
    return data
  },

  async clonarEquipo(payload: ClonarEquipoRequest): Promise<ClonarEquipoResponse> {
    const { data } = await api.post<ClonarEquipoResponse>('/api/equipos/clonar', payload)
    return data
  },

  async exportEquipos(filters: EquiposFilters = {}): Promise<Blob> {
    const { data } = await api.get<Blob>('/api/equipos/export', {
      params: filters,
      responseType: 'blob',
    })
    return data
  },
}
