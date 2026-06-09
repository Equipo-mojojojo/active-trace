/**
 * Tests for MonitorCoordinacionPage.
 *
 * Scenarios:
 * - Renderiza KPI cards con valores de la respuesta
 * - Renderiza la tabla con alumnos
 * - Estado vacío cuando no hay datos
 * - KPIs calculan correctamente atrasados y % al día
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
import { MonitorCoordinacionPage } from './MonitorCoordinacionPage'
import type { MonitorCoordResponse } from '../types/coordinacion.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MonitorCoordinacionPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockResponse: MonitorCoordResponse = {
  total: 3,
  limit: 20,
  offset: 0,
  entries: [
    {
      entrada_padron_id: 'ep-1',
      nombre: 'Ana',
      apellidos: 'López',
      comision: 'A',
      regional: 'Buenos Aires',
      materia_id: 'mat-1',
      aprobadas: 8,
      reprobadas: 1,
      faltantes: 1,
      atrasado: true,
    },
    {
      entrada_padron_id: 'ep-2',
      nombre: 'Bruno',
      apellidos: 'Martínez',
      comision: 'B',
      regional: null,
      materia_id: 'mat-1',
      aprobadas: 10,
      reprobadas: 0,
      faltantes: 0,
      atrasado: false,
    },
    {
      entrada_padron_id: 'ep-3',
      nombre: 'Carla',
      apellidos: 'Fernández',
      comision: 'A',
      regional: 'Córdoba',
      materia_id: 'mat-2',
      aprobadas: 5,
      reprobadas: 2,
      faltantes: 3,
      atrasado: true,
    },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('MonitorCoordinacionPage', () => {
  it('renderiza KPI cards con totales', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

    renderPage()

    await waitFor(() => {
      // Total alumnos — use getAllByText since "3" may appear multiple times
      const threes = screen.getAllByText('3')
      expect(threes.length).toBeGreaterThan(0)
    })

    // Con atrasos (2 de 3)
    const twos = screen.getAllByText('2')
    expect(twos.length).toBeGreaterThan(0)
    // % Al día (1/3 = 33%)
    expect(screen.getByText('33%')).toBeInTheDocument()
  })

  it('renderiza alumnos en la tabla', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Ana López')).toBeInTheDocument()
      expect(screen.getByText('Bruno Martínez')).toBeInTheDocument()
      expect(screen.getByText('Carla Fernández')).toBeInTheDocument()
    })

    // Badges de estado
    const atrasadoBadges = screen.getAllByText('Atrasado')
    expect(atrasadoBadges).toHaveLength(2)
    // "Al día" may appear in KPI label too; use getAllByText
    const alDias = screen.getAllByText('Al día')
    expect(alDias.length).toBeGreaterThan(0)
  })

  it('muestra estado vacío cuando no hay datos', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { total: 0, limit: 20, offset: 0, entries: [] },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no se encontraron alumnos/i)).toBeInTheDocument()
    })
  })

  it('muestra barras de progreso para actividades aprobadas', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse })

    renderPage()

    await waitFor(() => {
      // 8/10 para Ana, 10/10 para Bruno, 5/10 para Carla
      expect(screen.getByText('8/10')).toBeInTheDocument()
      expect(screen.getByText('10/10')).toBeInTheDocument()
      expect(screen.getByText('5/10')).toBeInTheDocument()
    })
  })
})
