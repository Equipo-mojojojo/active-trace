/**
 * Tests for MisComisionesPage.
 * TDD: tests written before/alongside implementation.
 *
 * Scenarios:
 * - Renderiza cards cuando hay comisiones
 * - Muestra estado vacío si no hay comisiones
 * - Muestra error si la API falla
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/shared/services/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { MisComisionesPage } from './MisComisionesPage'
import type { Comision } from '../types/profesor.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MisComisionesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockComisiones: Comision[] = [
  {
    id: 'mat-1',
    materia_id: 'mat-1',
    materia_nombre: 'Programación I',
    cohorte: '2024',
    comision: 'A',
    total_alumnos: 30,
    tiene_calificaciones: true,
  },
  {
    id: 'mat-2',
    materia_id: 'mat-2',
    materia_nombre: 'Matemática I',
    cohorte: '2024',
    comision: 'B',
    total_alumnos: 25,
    tiene_calificaciones: false,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('MisComisionesPage', () => {
  it('renderiza cards para cada comisión', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockComisiones })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Programación I')).toBeInTheDocument()
      expect(screen.getByText('Matemática I')).toBeInTheDocument()
    })

    // Badge de estado
    expect(screen.getByText('Importado')).toBeInTheDocument()
    expect(screen.getByText('Sin datos')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay comisiones', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/sin comisiones asignadas/i)).toBeInTheDocument()
    })
  })

  it('muestra mensaje de error cuando la API falla', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/error al cargar las comisiones/i)).toBeInTheDocument()
    })
  })
})
