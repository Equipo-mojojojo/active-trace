/**
 * Tests for comunicacionesService.
 * TDD: RED first — tests written before implementation.
 *
 * Scenarios:
 * - getPreviewMensaje: calls POST /api/v1/comunicaciones/preview
 * - enviarComunicacion: calls POST /api/v1/comunicaciones/lotes
 * - getLote: calls GET /api/v1/comunicaciones/lotes/{loteId}
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/shared/services/api', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { comunicacionesService } from './comunicacionesService'
import type {
  ComunicacionPreviewRequest,
  ComunicacionPreviewResponse,
  ComunicacionLoteResponse,
} from '../types/profesor.types'

const mockPreviewRequest: ComunicacionPreviewRequest = {
  materia_id: 'mat-1',
  entrada_padron_ids: ['ep-1', 'ep-2'],
  asunto_template: 'Estimado {nombre}',
  cuerpo_template: 'Estás atrasado en {materia}.',
}

const mockPreviewResponse: ComunicacionPreviewResponse = {
  requiere_aprobacion: false,
  preview: [
    {
      entrada_padron_id: 'ep-1',
      destinatario_nombre: 'Juan Perez',
      destinatario_email: 'juan@example.com',
      asunto: 'Estimado Juan',
      cuerpo: 'Estás atrasado en Programación I.',
    },
  ],
}

const mockLoteResponse: ComunicacionLoteResponse = {
  lote_id: 'lote-uuid-1',
  total: 2,
  requiere_aprobacion: false,
  comunicaciones: [
    {
      id: 'com-1',
      lote_id: 'lote-uuid-1',
      entrada_padron_id: 'ep-1',
      destinatario_nombre: 'Juan Perez',
      estado: 'PENDIENTE',
      requiere_aprobacion: false,
      aprobada: false,
      error_detalle: null,
    },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('comunicacionesService', () => {
  describe('getPreviewMensaje', () => {
    it('calls POST /api/v1/comunicaciones/preview with correct payload', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockPreviewResponse })

      const result = await comunicacionesService.getPreviewMensaje(mockPreviewRequest)

      expect(api.post).toHaveBeenCalledWith(
        '/comunicaciones/preview',
        mockPreviewRequest,
      )
      expect(result).toEqual(mockPreviewResponse)
    })

    it('returns requiere_aprobacion=true when tenant requires approval', async () => {
      const approvalResponse = { ...mockPreviewResponse, requiere_aprobacion: true }
      vi.mocked(api.post).mockResolvedValueOnce({ data: approvalResponse })

      const result = await comunicacionesService.getPreviewMensaje(mockPreviewRequest)
      expect(result.requiere_aprobacion).toBe(true)
    })
  })

  describe('enviarComunicacion', () => {
    it('calls POST /api/v1/comunicaciones/lotes with correct payload', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockLoteResponse })

      const result = await comunicacionesService.enviarComunicacion(mockPreviewRequest)

      expect(api.post).toHaveBeenCalledWith(
        '/comunicaciones/lotes',
        mockPreviewRequest,
      )
      expect(result).toEqual(mockLoteResponse)
    })

    it('propagates errors when API fails', async () => {
      vi.mocked(api.post).mockRejectedValueOnce(new Error('Server error'))

      await expect(
        comunicacionesService.enviarComunicacion(mockPreviewRequest),
      ).rejects.toThrow('Server error')
    })
  })

  describe('getLote', () => {
    it('calls GET /api/v1/comunicaciones/lotes/{loteId}', async () => {
      vi.mocked(api.get).mockResolvedValueOnce({ data: mockLoteResponse })

      const result = await comunicacionesService.getLote('lote-uuid-1')

      expect(api.get).toHaveBeenCalledWith('/comunicaciones/lotes/lote-uuid-1')
      expect(result).toEqual(mockLoteResponse)
    })

    it('propagates errors when lote not found', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('404 Not Found'))

      await expect(comunicacionesService.getLote('nonexistent')).rejects.toThrow('404 Not Found')
    })
  })
})
