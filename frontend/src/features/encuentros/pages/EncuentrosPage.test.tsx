/**
 * Tests for EncuentrosPage.
 *
 * Scenarios:
 * - Renderiza la lista de slots
 * - Muestra estado vacío
 * - Abre modal "Nuevo encuentro"
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { EncuentrosPage } from './EncuentrosPage'
import type { SlotEncuentro } from '../types/encuentros.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EncuentrosPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockSlots: SlotEncuentro[] = [
  {
    id: 'slot-1',
    asignacion_id: 'asig-1',
    materia_id: 'mat-1',
    titulo: 'Clase de Matemática I',
    hora: '10:00',
    dia_semana: 'Lunes',
    fecha_inicio: '2026-03-01',
    cant_semanas: 20,
    fecha_unica: null,
    meet_url: 'https://meet.google.com/abc',
    vig_desde: '2026-03-01',
    vig_hasta: '2026-12-01',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('EncuentrosPage', () => {
  it('renderiza la lista de slots', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: mockSlots })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Clase de Matemática I')).toBeInTheDocument()
      expect(screen.getByText('Recurrente')).toBeInTheDocument()
    })
  })

  it('muestra estado vacío cuando no hay slots', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no hay encuentros registrados/i)).toBeInTheDocument()
    })
  })

  it('abre modal al hacer click en "Nuevo encuentro"', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /nuevo encuentro/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /nuevo encuentro/i })).toBeInTheDocument()
    })
  })

  it('detecta encuentro único vs recurrente', async () => {
    const unicoSlot: SlotEncuentro = {
      ...mockSlots[0],
      id: 'slot-2',
      titulo: 'Examen único',
      cant_semanas: 0,
      fecha_unica: '2026-07-15',
    }
    vi.mocked(api.get).mockResolvedValue({ data: [mockSlots[0], unicoSlot] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Recurrente')).toBeInTheDocument()
      expect(screen.getByText('Único')).toBeInTheDocument()
    })
  })
})
