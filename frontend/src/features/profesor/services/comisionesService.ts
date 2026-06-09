/**
 * Service for calificaciones and analisis API calls for the professor module.
 *
 * Endpoints:
 *  GET  /api/v1/analisis/atrasados           — F2.2
 *  GET  /api/v1/analisis/ranking             — F2.3
 *  GET  /api/v1/analisis/notas-finales       — F2.5
 *  GET  /api/v1/analisis/export/sin-corregir — F2.6 (CSV)
 *  POST /api/v1/calificaciones/preview       — parse file, no DB write
 *  POST /api/v1/calificaciones/import        — import selected activities
 *  PUT  /api/v1/calificaciones/umbral        — configure threshold
 */
import { api } from '@/shared/services/api'
import type {
  AtrasadosResponse,
  RankingResponse,
  NotasFinalResponse,
  PreviewCalificacionesResponse,
  ImportCalificacionesResponse,
  UmbralMateriaRequest,
  UmbralMateriaResponse,
} from '../types/profesor.types'

export const comisionesService = {
  async getAtrasados(materiaId: string): Promise<AtrasadosResponse> {
    const { data } = await api.get<AtrasadosResponse>('/analisis/atrasados', {
      params: { materia_id: materiaId },
    })
    return data
  },

  async getRanking(materiaId: string): Promise<RankingResponse> {
    const { data } = await api.get<RankingResponse>('/analisis/ranking', {
      params: { materia_id: materiaId },
    })
    return data
  },

  async getNotasFinales(materiaId: string): Promise<NotasFinalResponse> {
    const { data } = await api.get<NotasFinalResponse>('/analisis/notas-finales', {
      params: { materia_id: materiaId },
    })
    return data
  },

  async exportSinCorregir(materiaId: string): Promise<Blob> {
    const { data } = await api.get<Blob>('/analisis/export/sin-corregir', {
      params: { materia_id: materiaId },
      responseType: 'blob',
    })
    return data
  },

  async previewCalificaciones(
    materiaId: string,
    file: File,
  ): Promise<PreviewCalificacionesResponse> {
    const formData = new FormData()
    formData.append('materia_id', materiaId)
    formData.append('file', file)

    const { data } = await api.post<PreviewCalificacionesResponse>(
      '/calificaciones/preview',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return data
  },

  async importarCalificaciones(
    materiaId: string,
    file: File,
    actividadesSeleccionadas: string[],
    asignacionId?: string,
  ): Promise<ImportCalificacionesResponse> {
    const formData = new FormData()
    formData.append('materia_id', materiaId)
    formData.append('file', file)
    actividadesSeleccionadas.forEach((act) =>
      formData.append('actividades_seleccionadas', act),
    )
    if (asignacionId) {
      formData.append('asignacion_id', asignacionId)
    }

    const { data } = await api.post<ImportCalificacionesResponse>(
      '/calificaciones/import',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return data
  },

  async configurarUmbral(payload: UmbralMateriaRequest): Promise<UmbralMateriaResponse> {
    const { data } = await api.put<UmbralMateriaResponse>(
      '/calificaciones/umbral',
      payload,
    )
    return data
  },
}
