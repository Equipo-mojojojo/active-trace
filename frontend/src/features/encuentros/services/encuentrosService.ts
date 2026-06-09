/**
 * Service for encuentros y guardias API calls.
 *
 * Endpoints (backend/app/api/v1/routers/encuentros.py):
 *  GET  /api/v1/encuentros/slots                    — List slots
 *  POST /api/v1/encuentros/slots                    — Create slot (recurrente o único)
 *  GET  /api/v1/encuentros/instancias               — List instancias
 *  PATCH /api/v1/encuentros/instancias/{id}          — Update instancia
 *
 * Endpoints (backend/app/api/v1/routers/guardias.py):
 *  GET  /api/v1/guardias                            — List guardias
 *  GET  /api/v1/guardias/export                     — CSV export
 */
import { api } from '@/shared/services/api'
import type {
  SlotEncuentro,
  SlotEncuentroCreate,
  InstanciaEncuentro,
  InstanciaEncuentroUpdate,
  Guardia,
  EncuentrosFilters,
  GuardiasFilters,
} from '../types/encuentros.types'

export const encuentrosService = {
  async getEncuentros(filters: EncuentrosFilters = {}): Promise<SlotEncuentro[]> {
    const { data } = await api.get<SlotEncuentro[]>('/encuentros/slots', {
      params: filters,
    })
    return data
  },

  async createEncuentro(payload: SlotEncuentroCreate): Promise<SlotEncuentro> {
    const { data } = await api.post<SlotEncuentro>('/encuentros/slots', payload)
    return data
  },

  async getInstancias(filters: EncuentrosFilters = {}): Promise<InstanciaEncuentro[]> {
    const { data } = await api.get<InstanciaEncuentro[]>('/encuentros/instancias', {
      params: filters,
    })
    return data
  },

  async updateInstancia(id: string, payload: InstanciaEncuentroUpdate): Promise<InstanciaEncuentro> {
    const { data } = await api.patch<InstanciaEncuentro>(
      `/encuentros/instancias/${id}`,
      payload,
    )
    return data
  },

  async getGuardias(filters: GuardiasFilters = {}): Promise<Guardia[]> {
    const { data } = await api.get<Guardia[]>('/guardias', { params: filters })
    return data
  },

  async exportGuardias(filters: GuardiasFilters = {}): Promise<Blob> {
    const { data } = await api.get<Blob>('/guardias/export', {
      params: filters,
      responseType: 'blob',
    })
    return data
  },
}
