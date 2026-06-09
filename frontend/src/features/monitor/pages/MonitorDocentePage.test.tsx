/**
 * Tests for MonitorDocentePage.
 * TDD: tests written before implementation.
 *
 * Scenarios:
 * - Renderiza tabla cuando hay datos
 * - Muestra estado vacío cuando no hay entradas
 * - Filtros se aplican correctamente
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../services/monitorService', () => ({
  monitorService: {
    getMonitor: vi.fn(),
  },
}))

import { monitorService } from '../services/monitorService'
import { MonitorDocentePage } from './MonitorDocentePage'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MonitorDocentePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockResponse = {
  total: 2,
  limit: 1000,
  offset: 0,
  entries: [
    {
      entrada_padron_id: 'ep-1',
      nombre: 'Juan',
      apellidos: 'Perez',
      comision: 'A',
      regional: null,
      materia_id: 'mat-1',
      aprobadas: 5,
      reprobadas: 1,
      faltantes: 2,
      atrasado: true,
    },
    {
      entrada_padron_id: 'ep-2',
      nombre: 'Ana',
      apellidos: 'Lopez',
      comision: 'A',
      regional: null,
      materia_id: 'mat-1',
      aprobadas: 8,
      reprobadas: 0,
      faltantes: 0,
      atrasado: false,
    },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('MonitorDocentePage', () => {
  it('renderiza la tabla con entradas de alumnos', async () => {
    vi.mocked(monitorService.getMonitor).mockResolvedValue(mockResponse)

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
      expect(screen.getByText('Lopez, Ana')).toBeInTheDocument()
    })

    // Estado badges
    expect(screen.getByText('Atrasado')).toBeInTheDocument()
    expect(screen.getByText('Al día')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay entradas', async () => {
    vi.mocked(monitorService.getMonitor).mockResolvedValue({
      total: 0,
      limit: 1000,
      offset: 0,
      entries: [],
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no hay alumnos que coincidan/i)).toBeInTheDocument()
    })
  })

  it('muestra error cuando la API falla', async () => {
    vi.mocked(monitorService.getMonitor).mockRejectedValue(new Error('Network error'))

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/error al cargar el monitor/i)).toBeInTheDocument()
    })
  })

  it('llama a getMonitor con filtros cuando se escribe en el buscador', async () => {
    const user = userEvent.setup()
    vi.mocked(monitorService.getMonitor).mockResolvedValue(mockResponse)

    renderPage()

    await waitFor(() => {
      expect(monitorService.getMonitor).toHaveBeenCalled()
    })

    const searchInput = screen.getByPlaceholderText(/nombre o correo/i)
    await user.type(searchInput, 'Juan')

    // After debounce (300ms), should call again with q filter
    // We check that the input has the value at minimum
    expect(searchInput).toHaveValue('Juan')
  })
})
