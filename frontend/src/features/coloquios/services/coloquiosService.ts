/**
 * Service for coloquios / evaluaciones API calls.
 *
 * Endpoints (backend/app/api/v1/routers/coloquios.py):
 *  GET  /api/v1/coloquios                              — List evaluaciones
 *  POST /api/v1/coloquios                              — Create convocatoria
 *  GET  /api/v1/coloquios/{id}                         — Get convocatoria detail
 *  POST /api/v1/coloquios/{id}/cerrar                  — Cerrar convocatoria
 *  GET  /api/v1/coloquios/{id}/convocados               — List convocados
 *  POST /api/v1/coloquios/{id}/convocados               — Import convocados
 *  GET  /api/v1/coloquios/{id}/reservas                 — List reservas
 *  GET  /api/v1/coloquios/{id}/resultados               — List resultados
 *  POST /api/v1/coloquios/{id}/resultados               — Save resultado
 */
import { api } from '@/shared/services/api'
import type {
  Convocatoria,
  ConvocatoriaCreate,
  ConvocatoriaMetrics,
  Convocado,
  Reserva,
  Resultado,
  ResultadoCreate,
} from '../types/coloquios.types'

export const coloquiosService = {
  async getColoquios(): Promise<Convocatoria[]> {
    const { data } = await api.get<Convocatoria[]>('/coloquios')
    return data
  },

  async createConvocatoria(payload: ConvocatoriaCreate): Promise<Convocatoria> {
    const { data } = await api.post<Convocatoria>('/coloquios', payload)
    return data
  },

  async getConvocatoriaDetail(id: string): Promise<Convocatoria> {
    const { data } = await api.get<Convocatoria>(`/coloquios/${id}`)
    return data
  },

  async getMetricas(id: string): Promise<ConvocatoriaMetrics> {
    const { data } = await api.get<ConvocatoriaMetrics>(`/coloquios/${id}/metricas`)
    return data
  },

  async importConvocados(id: string, alumnoIds: string[]): Promise<Convocado[]> {
    const { data } = await api.post<Convocado[]>(`/coloquios/${id}/convocados`, {
      alumno_ids: alumnoIds,
    })
    return data
  },

  async getReservas(id: string): Promise<Reserva[]> {
    const { data } = await api.get<Reserva[]>(`/coloquios/${id}/reservas`)
    return data
  },

  async getResultados(id: string): Promise<Resultado[]> {
    const { data } = await api.get<Resultado[]>(`/coloquios/${id}/resultados`)
    return data
  },

  async saveResultado(convId: string, payload: ResultadoCreate): Promise<Resultado> {
    const { data } = await api.post<Resultado>(`/coloquios/${convId}/resultados`, payload)
    return data
  },

  async cerrarConvocatoria(id: string): Promise<Convocatoria> {
    const { data } = await api.post<Convocatoria>(`/coloquios/${id}/cerrar`)
    return data
  },
}
