/**
 * Tests for GrillaSalarialPage — TDD Strict
 *
 * Scenarios:
 * - Listar salarios base
 * - Crear inline (POST)
 * - Editar inline (PUT)
 * - 409 solapamiento conserva datos
 * - Vigencia abierta (hasta vacío)
 * - Oculto sin permiso (guard de ruta, no componente)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { GrillaSalarialPage } from './GrillaSalarialPage'

vi.mock('../hooks/useGrillaSalarial', () => ({
  useSalarioBase: vi.fn(),
  useCreateSalarioBase: vi.fn(),
  useUpdateSalarioBase: vi.fn(),
  useDeleteSalarioBase: vi.fn(),
  useSalarioPlus: vi.fn(),
  useCreateSalarioPlus: vi.fn(),
  useUpdateSalarioPlus: vi.fn(),
  useDeleteSalarioPlus: vi.fn(),
}))

import {
  useSalarioBase,
  useCreateSalarioBase,
  useUpdateSalarioBase,
  useDeleteSalarioBase,
  useSalarioPlus,
  useCreateSalarioPlus,
  useUpdateSalarioPlus,
  useDeleteSalarioPlus,
} from '../hooks/useGrillaSalarial'

const mockSalarios: import('../types/finanzas.types').SalarioBase[] = [
  { id: 's1', rol: 'PROFESOR', monto: 60000, vigencia_desde: '2024-01-01', vigencia_hasta: null },
  { id: 's2', rol: 'TUTOR', monto: 40000, vigencia_desde: '2024-01-01', vigencia_hasta: '2024-12-31' },
]

const noopMutation = () => ({
  mutateAsync: vi.fn(),
  isPending: false,
})

function setupMocks(opts: { createBaseAsync?: () => Promise<unknown> } = {}) {
  vi.mocked(useSalarioBase).mockReturnValue({
    data: mockSalarios,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useSalarioBase>)

  vi.mocked(useCreateSalarioBase).mockReturnValue({
    ...noopMutation(),
    mutateAsync: opts.createBaseAsync ?? vi.fn().mockResolvedValue({}),
  } as ReturnType<typeof useCreateSalarioBase>)

  vi.mocked(useUpdateSalarioBase).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateSalarioBase>)
  vi.mocked(useDeleteSalarioBase).mockReturnValue(noopMutation() as ReturnType<typeof useDeleteSalarioBase>)

  vi.mocked(useSalarioPlus).mockReturnValue({
    data: [],
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useSalarioPlus>)

  vi.mocked(useCreateSalarioPlus).mockReturnValue(noopMutation() as ReturnType<typeof useCreateSalarioPlus>)
  vi.mocked(useUpdateSalarioPlus).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateSalarioPlus>)
  vi.mocked(useDeleteSalarioPlus).mockReturnValue(noopMutation() as ReturnType<typeof useDeleteSalarioPlus>)
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GrillaSalarialPage — listar salarios base', () => {
  it('muestra las filas de salarios base con rol badge', () => {
    setupMocks()
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('PROFESOR')).toBeInTheDocument()
    expect(screen.getByText('TUTOR')).toBeInTheDocument()
  })

  it('muestra — para vigencia_hasta nula', () => {
    setupMocks()
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThan(0)
  })
})

describe('GrillaSalarialPage — crear inline', () => {
  it('al hacer click en Nueva fila muestra la fila de edición', () => {
    setupMocks()
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva fila salario base' }))

    expect(screen.getByPlaceholderText('Monto')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Desde')).toBeInTheDocument()
  })

  it('al hacer click en Guardar llama a createBase.mutateAsync', async () => {
    const createBaseAsync = vi.fn().mockResolvedValue({})
    setupMocks({ createBaseAsync })
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva fila salario base' }))
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => {
      expect(createBaseAsync).toHaveBeenCalled()
    })
  })
})

describe('GrillaSalarialPage — 409 solapamiento', () => {
  it('al recibir 409 muestra error inline y conserva los datos', async () => {
    const error409 = Object.assign(new Error('409'), { response: { status: 409 } })
    const createBaseAsync = vi.fn().mockRejectedValue(error409)
    setupMocks({ createBaseAsync })
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva fila salario base' }))

    const montoInput = screen.getByPlaceholderText('Monto')
    fireEvent.change(montoInput, { target: { value: '75000' } })

    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => {
      expect(screen.getByText(/Solapamiento de vigencia/i)).toBeInTheDocument()
    })
    // Data is preserved
    expect(montoInput).toHaveValue(75000)
  })
})

describe('GrillaSalarialPage — vigencia abierta', () => {
  it('la fila con vigencia_hasta nula muestra —', () => {
    setupMocks()
    render(<GrillaSalarialPage />, { wrapper: makeWrapper() })

    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})
