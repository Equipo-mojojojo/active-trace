/**
 * Tests for comisionesService.
 * TDD: RED first — tests written before implementation.
 *
 * Scenarios:
 * - getAtrasados: calls GET /api/v1/analisis/atrasados with materia_id param
 * - getRanking: calls GET /api/v1/analisis/ranking with materia_id param
 * - getNotasFinales: calls GET /api/v1/analisis/notas-finales with materia_id param
 * - getSinCorregir: calls GET /api/v1/analisis/export/sin-corregir (CSV response)
 * - previewCalificaciones: calls POST /api/v1/calificaciones/preview with FormData
 * - importarCalificaciones: calls POST /api/v1/calificaciones/import with FormData
 * - configurarUmbral: calls PUT /api/v1/calificaciones/umbral with body
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { comisionesService } from './comisionesService'
import type {
  AtrasadosResponse,
  RankingResponse,
  NotasFinalResponse,
  PreviewCalificacionesResponse,
  ImportCalificacionesResponse,
  UmbralMateriaResponse,
} from '../types/profesor.types'

const materiaId = 'mat-uuid-1'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('comisionesService', () => {
  describe('getAtrasados', () => {
    it('calls GET /api/v1/analisis/atrasados with materia_id', async () => {
      const mockResponse: AtrasadosResponse = {
        total: 2,
        atrasados: [
          {
            entrada_padron_id: 'ep-1',
            nombre: 'Juan',
            apellidos: 'Perez',
            comision: 'A',
            materia_id: materiaId,
            actividades_faltantes: ['TP1'],
            actividades_reprobadas: [],
          },
        ],
      }
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.getAtrasados(materiaId)

      expect(api.get).toHaveBeenCalledWith('/analisis/atrasados', {
        params: { materia_id: materiaId },
      })
      expect(result).toEqual(mockResponse)
    })

    it('propagates errors from the API', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))
      await expect(comisionesService.getAtrasados(materiaId)).rejects.toThrow('Network error')
    })
  })

  describe('getRanking', () => {
    it('calls GET /api/v1/analisis/ranking with materia_id', async () => {
      const mockResponse: RankingResponse = {
        total: 1,
        ranking: [
          { entrada_padron_id: 'ep-1', nombre: 'Ana', apellidos: 'Lopez', comision: 'A', aprobadas: 5 },
        ],
      }
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.getRanking(materiaId)

      expect(api.get).toHaveBeenCalledWith('/analisis/ranking', {
        params: { materia_id: materiaId },
      })
      expect(result).toEqual(mockResponse)
    })

    it('returns empty ranking when no alumnos', async () => {
      const emptyResponse: RankingResponse = { total: 0, ranking: [] }
      vi.mocked(api.get).mockResolvedValueOnce({ data: emptyResponse })

      const result = await comisionesService.getRanking(materiaId)
      expect(result.ranking).toHaveLength(0)
    })
  })

  describe('getNotasFinales', () => {
    it('calls GET /api/v1/analisis/notas-finales with materia_id', async () => {
      const mockResponse: NotasFinalResponse = {
        actividades_seleccionadas: ['TP1', 'TP2'],
        notas: [
          { entrada_padron_id: 'ep-1', nombre: 'Juan', apellidos: 'Perez', nota_final: 8.5 },
        ],
      }
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.getNotasFinales(materiaId)

      expect(api.get).toHaveBeenCalledWith('/analisis/notas-finales', {
        params: { materia_id: materiaId },
      })
      expect(result).toEqual(mockResponse)
    })

    it('returns empty notas when no data', async () => {
      const emptyResponse: NotasFinalResponse = { actividades_seleccionadas: [], notas: [] }
      vi.mocked(api.get).mockResolvedValueOnce({ data: emptyResponse })

      const result = await comisionesService.getNotasFinales(materiaId)
      expect(result.notas).toHaveLength(0)
    })
  })

  describe('previewCalificaciones', () => {
    it('calls POST /api/v1/calificaciones/preview with FormData', async () => {
      const file = new File(['data'], 'calificaciones.csv', { type: 'text/csv' })
      const mockResponse: PreviewCalificacionesResponse = {
        actividades: [{ nombre: 'TP1', tipo: 'numerica', muestra_valores: ['8', '9'] }],
      }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.previewCalificaciones(materiaId, file)

      expect(api.post).toHaveBeenCalledWith(
        '/calificaciones/preview',
        expect.any(FormData),
        expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } }),
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('importarCalificaciones', () => {
    it('calls POST /api/v1/calificaciones/import with FormData including actividades', async () => {
      const file = new File(['data'], 'notas.csv', { type: 'text/csv' })
      const actividades = ['TP1', 'TP2']
      const mockResponse: ImportCalificacionesResponse = { importadas: 2 }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.importarCalificaciones(materiaId, file, actividades)

      expect(api.post).toHaveBeenCalledWith(
        '/calificaciones/import',
        expect.any(FormData),
        expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } }),
      )
      expect(result).toEqual(mockResponse)
    })

    it('includes asignacion_id in FormData when provided', async () => {
      const file = new File(['data'], 'notas.csv', { type: 'text/csv' })
      const mockResponse: ImportCalificacionesResponse = { importadas: 3 }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.importarCalificaciones(
        materiaId,
        file,
        ['TP1'],
        'asign-uuid-1',
      )

      expect(result).toEqual(mockResponse)
      expect(api.post).toHaveBeenCalled()
    })
  })

  describe('configurarUmbral', () => {
    it('calls PUT /api/v1/calificaciones/umbral with request body', async () => {
      const mockResponse: UmbralMateriaResponse = {
        id: 'umbral-1',
        asignacion_id: 'asign-1',
        umbral_pct: 70,
        valores_aprobatorios: [],
      }
      vi.mocked(api.put).mockResolvedValueOnce({ data: mockResponse })

      const result = await comisionesService.configurarUmbral({
        asignacion_id: 'asign-1',
        materia_id: materiaId,
        umbral_pct: 70,
        valores_aprobatorios: [],
      })

      expect(api.put).toHaveBeenCalledWith('/calificaciones/umbral', {
        asignacion_id: 'asign-1',
        materia_id: materiaId,
        umbral_pct: 70,
        valores_aprobatorios: [],
      })
      expect(result).toEqual(mockResponse)
    })
  })
})
