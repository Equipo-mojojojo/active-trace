/**
 * Service for comunicaciones API calls (C-12 backend).
 *
 * Endpoints:
 *  POST /api/v1/comunicaciones/preview        — preview personalizado por alumno
 *  POST /api/v1/comunicaciones/lotes          — crear lote y encolar envíos
 *  GET  /api/v1/comunicaciones/lotes/{id}     — estado del lote (para polling)
 */
import { api } from '@/shared/services/api'
import type {
  ComunicacionPreviewRequest,
  ComunicacionPreviewResponse,
  ComunicacionLoteResponse,
} from '../types/profesor.types'

export const comunicacionesService = {
  async getPreviewMensaje(
    payload: ComunicacionPreviewRequest,
  ): Promise<ComunicacionPreviewResponse> {
    const { data } = await api.post<ComunicacionPreviewResponse>(
      '/comunicaciones/preview',
      payload,
    )
    return data
  },

  async enviarComunicacion(
    payload: ComunicacionPreviewRequest,
  ): Promise<ComunicacionLoteResponse> {
    const { data } = await api.post<ComunicacionLoteResponse>(
      '/comunicaciones/lotes',
      payload,
    )
    return data
  },

  async getLote(loteId: string): Promise<ComunicacionLoteResponse> {
    const { data } = await api.get<ComunicacionLoteResponse>(
      `/comunicaciones/lotes/${loteId}`,
    )
    return data
  },
}
