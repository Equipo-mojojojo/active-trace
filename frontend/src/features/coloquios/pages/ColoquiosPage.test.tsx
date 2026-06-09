/**
 * Tests for ColoquiosPage.
 *
 * Scenarios:
 * - Renderiza lista de convocatorias
 * - Estado vacío cuando no hay convocatorias
 * - Abre modal de nueva convocatoria
 * - Validación de cupo > 0
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { ColoquiosPage } from './ColoquiosPage'
import type { Convocatoria } from '../types/coloquios.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ColoquiosPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockConvocatorias: Convocatoria[] = [
  {
    id: 'conv-1',
    materia_id: 'mat-aaaaaaa1',
    cohorte_id: 'coh-1',
    tipo: 'Coloquio',
    instancia: '1ra',
    dias_disponibles: 7,
    estado: 'Abierta',
    turnos: [],
  },
  {
    id: 'conv-2',
    materia_id: 'mat-bbbbbbb2',
    cohorte_id: 'coh-1',
    tipo: 'Coloquio',
    instancia: '2da',
    dias_disponibles: 7,
    estado: 'Cerrada',
    turnos: [],
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ColoquiosPage', () => {
  it('renderiza lista de convocatorias', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: mockConvocatorias }) // coloquios
      .mockResolvedValue({ data: {} }) // metricas

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('1ra')).toBeInTheDocument()
      expect(screen.getByText('2da')).toBeInTheDocument()
      expect(screen.getByText('Abierta')).toBeInTheDocument()
      expect(screen.getByText('Cerrada')).toBeInTheDocument()
    })
  })

  it('muestra estado vacío cuando no hay convocatorias', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no hay convocatorias/i)).toBeInTheDocument()
    })
  })

  it('abre modal al hacer click en "Nueva convocatoria"', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /nueva convocatoria/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /nueva convocatoria/i })).toBeInTheDocument()
    })
  })

  it('no llama a la API si el cupo es 0 al intentar crear', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: {} })

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /nueva convocatoria/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Fill required UUID fields
    const textInputs = screen.getAllByPlaceholderText('UUID')
    fireEvent.change(textInputs[0], { target: { value: '11111111-1111-1111-1111-111111111111' } })
    fireEvent.change(textInputs[1], { target: { value: '22222222-2222-2222-2222-222222222222' } })

    // Set cupo to 0 (spinbutton)
    const spinButtons = screen.getAllByRole('spinbutton')
    const cupoInput = spinButtons[spinButtons.length - 1]
    fireEvent.change(cupoInput, { target: { value: '0' } })

    // Try to submit — zod should block it
    fireEvent.click(screen.getByRole('button', { name: /crear convocatoria/i }))

    // API post should NOT have been called (validation failed)
    await new Promise((r) => setTimeout(r, 100))
    expect(api.post).not.toHaveBeenCalledWith(
      expect.stringContaining('/coloquios'),
      expect.anything(),
    )
  })
})
