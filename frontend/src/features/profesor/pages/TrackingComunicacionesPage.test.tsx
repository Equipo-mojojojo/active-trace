/**
 * Tests for TrackingComunicacionesPage.
 * TDD: tests written before implementation.
 *
 * Scenarios:
 * - Muestra mensaje cuando no hay loteId
 * - Muestra contadores con datos reales
 * - Filtro por estado funciona
 * - Polling indicado cuando hay estados no-terminales
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../services/comunicacionesService', () => ({
  comunicacionesService: {
    getLote: vi.fn(),
    getPreviewMensaje: vi.fn(),
    enviarComunicacion: vi.fn(),
  },
}))

import { comunicacionesService } from '../services/comunicacionesService'
import { TrackingComunicacionesPage } from './TrackingComunicacionesPage'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage(loteId?: string) {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={[
          { pathname: '/profesor/comunicacion/tracking', state: loteId ? { loteId } : undefined },
        ]}
      >
        <Routes>
          <Route path="/profesor/comunicacion/tracking" element={<TrackingComunicacionesPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockLote = {
  lote_id: 'lote-1',
  total: 3,
  requiere_aprobacion: false,
  comunicaciones: [
    {
      id: 'c-1',
      lote_id: 'lote-1',
      entrada_padron_id: 'ep-1',
      destinatario_nombre: 'Juan Perez',
      estado: 'OK',
      requiere_aprobacion: false,
      aprobada: true,
      error_detalle: null,
    },
    {
      id: 'c-2',
      lote_id: 'lote-1',
      entrada_padron_id: 'ep-2',
      destinatario_nombre: 'Maria Garcia',
      estado: 'PENDIENTE',
      requiere_aprobacion: false,
      aprobada: false,
      error_detalle: null,
    },
    {
      id: 'c-3',
      lote_id: 'lote-1',
      entrada_padron_id: 'ep-3',
      destinatario_nombre: 'Carlos Lopez',
      estado: 'FALLIDO',
      requiere_aprobacion: false,
      aprobada: false,
      error_detalle: 'Mailbox full',
    },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TrackingComunicacionesPage', () => {
  it('muestra mensaje informativo cuando no hay loteId', () => {
    renderPage()

    expect(screen.getByText(/no hay lote seleccionado/i)).toBeInTheDocument()
  })

  it('muestra contadores resumen cuando hay datos', async () => {
    vi.mocked(comunicacionesService.getLote).mockResolvedValue(mockLote)

    renderPage('lote-1')

    await waitFor(() => {
      // Labels for counters
      expect(screen.getByText('Enviados')).toBeInTheDocument()
      expect(screen.getByText('Pendientes')).toBeInTheDocument()
      expect(screen.getByText('Fallidos')).toBeInTheDocument()
    })
  })

  it('filtra comunicaciones por estado', async () => {
    const user = userEvent.setup()
    vi.mocked(comunicacionesService.getLote).mockResolvedValue(mockLote)

    renderPage('lote-1')

    await waitFor(() => {
      const rows = screen.getAllByTestId('tracking-row')
      expect(rows.length).toBeGreaterThan(0)
    })

    // Initially 3 rows
    expect(screen.getAllByTestId('tracking-row')).toHaveLength(3)

    // Select "Fallido" filter
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'FALLIDO')

    await waitFor(() => {
      const rows = screen.getAllByTestId('tracking-row')
      expect(rows).toHaveLength(1)
      expect(screen.getByText('Carlos Lopez')).toBeInTheDocument()
    })
  })

  it('muestra indicador de polling cuando hay estados no-terminales', async () => {
    vi.mocked(comunicacionesService.getLote).mockResolvedValue(mockLote)

    renderPage('lote-1')

    await waitFor(() => {
      // PENDIENTE comunicacion → shows polling indicator
      expect(screen.getByText(/actualizando cada 5s/i)).toBeInTheDocument()
    })
  })
})
