/**
 * Tests for useImportarCalificaciones hook.
 * TDD: tests for state machine behavior.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { createElement } from 'react'

vi.mock('../services/comisionesService', () => ({
  comisionesService: {
    previewCalificaciones: vi.fn(),
    importarCalificaciones: vi.fn(),
    getAtrasados: vi.fn(),
    getRanking: vi.fn(),
    getNotasFinales: vi.fn(),
  },
}))

import { comisionesService } from '../services/comisionesService'
import { useImportarCalificaciones } from './useImportarCalificaciones'

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children)
}

const mockPreviewResponse = {
  actividades: [
    { nombre: 'TP1', tipo: 'numerica' as const, muestra_valores: ['8', '9'] },
    { nombre: 'TP2', tipo: 'textual' as const, muestra_valores: ['Sí'] },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useImportarCalificaciones', () => {
  it('inicia en step "upload" sin actividades', () => {
    const { result } = renderHook(() => useImportarCalificaciones('mat-1'), {
      wrapper: makeWrapper(),
    })

    expect(result.current.step).toBe('upload')
    expect(result.current.actividadesDetectadas).toHaveLength(0)
    expect(result.current.seleccionadas).toHaveLength(0)
    expect(result.current.error).toBeNull()
  })

  it('avanza a step "preview" después de subir un archivo', async () => {
    vi.mocked(comisionesService.previewCalificaciones).mockResolvedValue(mockPreviewResponse)

    const { result } = renderHook(() => useImportarCalificaciones('mat-1'), {
      wrapper: makeWrapper(),
    })

    const file = new File(['data'], 'notas.csv', { type: 'text/csv' })

    act(() => {
      result.current.uploadFile(file)
    })

    await waitFor(() => {
      expect(result.current.step).toBe('preview')
    })

    expect(result.current.actividadesDetectadas).toHaveLength(2)
    expect(result.current.seleccionadas).toEqual(['TP1', 'TP2'])
  })

  it('setea error cuando el upload falla', async () => {
    vi.mocked(comisionesService.previewCalificaciones).mockRejectedValue(
      new Error('Formato inválido'),
    )

    const { result } = renderHook(() => useImportarCalificaciones('mat-1'), {
      wrapper: makeWrapper(),
    })

    const file = new File(['data'], 'notas.pdf', { type: 'application/pdf' })

    act(() => {
      result.current.uploadFile(file)
    })

    await waitFor(() => {
      expect(result.current.error).toBe('Formato inválido')
    })

    expect(result.current.step).toBe('upload')
  })

  it('toggleActividad agrega y quita nombres del array seleccionadas', async () => {
    vi.mocked(comisionesService.previewCalificaciones).mockResolvedValue(mockPreviewResponse)

    const { result } = renderHook(() => useImportarCalificaciones('mat-1'), {
      wrapper: makeWrapper(),
    })

    const file = new File(['data'], 'notas.csv')
    act(() => { result.current.uploadFile(file) })
    await waitFor(() => { expect(result.current.step).toBe('preview') })

    // Deselect TP1
    act(() => { result.current.toggleActividad('TP1') })
    expect(result.current.seleccionadas).toEqual(['TP2'])

    // Re-select TP1
    act(() => { result.current.toggleActividad('TP1') })
    expect(result.current.seleccionadas).toContain('TP1')
  })

  it('goBack vuelve de preview a upload', async () => {
    vi.mocked(comisionesService.previewCalificaciones).mockResolvedValue(mockPreviewResponse)

    const { result } = renderHook(() => useImportarCalificaciones('mat-1'), {
      wrapper: makeWrapper(),
    })

    const file = new File(['data'], 'notas.csv')
    act(() => { result.current.uploadFile(file) })
    await waitFor(() => { expect(result.current.step).toBe('preview') })

    act(() => { result.current.goBack() })
    expect(result.current.step).toBe('upload')
  })
})
