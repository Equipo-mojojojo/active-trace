/**
 * Service for avisos institucionales API calls.
 *
 * Endpoints (backend/app/api/v1/routers/avisos.py):
 *  GET   /api/v1/avisos           — List all avisos (COORDINADOR)
 *  POST  /api/v1/avisos           — Create aviso
 *  PATCH /api/v1/avisos/{id}      — Update / archivar aviso (activo=false)
 *  POST  /api/v1/avisos/{id}/ack  — Acknowledge aviso (destinatario)
 */
import { api } from '@/shared/services/api'
import type { Aviso, AvisoCreate } from '../types/coordinacion.types'

export const avisosService = {
  async getAvisos(): Promise<Aviso[]> {
    const { data } = await api.get<Aviso[]>('/avisos')
    return data
  },

  async getMisAvisos(): Promise<Aviso[]> {
    const { data } = await api.get<Aviso[]>('/avisos/mis-avisos')
    return data
  },

  async createAviso(payload: AvisoCreate): Promise<Aviso> {
    const { data } = await api.post<Aviso>('/avisos', payload)
    return data
  },

  async archivarAviso(id: string): Promise<Aviso> {
    const { data } = await api.patch<Aviso>(`/avisos/${id}`, { activo: false })
    return data
  },

  async ackAviso(id: string): Promise<void> {
    await api.post(`/avisos/${id}/ack`)
  },
}
