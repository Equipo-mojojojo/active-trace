/**
 * Tests for ComisionPage.
 * TDD: tests for main rendering and interactions.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../services/comisionesService', () => ({
  comisionesService: {
    getAtrasados: vi.fn(),
    getRanking: vi.fn(),
    getNotasFinales: vi.fn(),
    exportSinCorregir: vi.fn(),
    configurarUmbral: vi.fn(),
    previewCalificaciones: vi.fn(),
    importarCalificaciones: vi.fn(),
  },
}))

import { comisionesService } from '../services/comisionesService'
import { ComisionPage } from './ComisionPage'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
}

function renderPage(comisionId = 'mat-1') {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={[`/profesor/comisiones/${comisionId}`]}
      >
        <Routes>
          <Route path="/profesor/comisiones/:comisionId" element={<ComisionPage />} />
          <Route
            path="/profesor/comisiones/:comisionId/importar"
            element={<div>Importar Page</div>}
          />
          <Route
            path="/profesor/comunicacion/:comisionId"
            element={<div>Comunicacion Page</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockAtrasados = { total: 1, atrasados: [
  {
    entrada_padron_id: 'ep-1',
    nombre: 'Juan',
    apellidos: 'Perez',
    comision: 'A',
    materia_id: 'mat-1',
    actividades_faltantes: ['TP1'],
    actividades_reprobadas: [],
  },
]}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(comisionesService.getAtrasados).mockResolvedValue(mockAtrasados)
  vi.mocked(comisionesService.getRanking).mockResolvedValue({ total: 0, ranking: [] })
  vi.mocked(comisionesService.getNotasFinales).mockResolvedValue({
    actividades_seleccionadas: [],
    notas: [],
  })
  vi.mocked(comisionesService.configurarUmbral).mockResolvedValue({
    id: 'umbral-1',
    asignacion_id: 'mat-1',
    umbral_pct: 75,
    valores_aprobatorios: [],
  })
})

describe('ComisionPage', () => {
  it('renderiza el header de comisión', () => {
    renderPage()

    expect(screen.getByText('Comisión')).toBeInTheDocument()
  })

  it('renderiza el UmbralSlider con valor por defecto 60', () => {
    renderPage()

    expect(screen.getByText('Umbral de aprobación')).toBeInTheDocument()
    const sliderInput = screen.getByRole('spinbutton')
    expect(sliderInput).toHaveValue(60)
  })

  it('renderiza los tabs de análisis', async () => {
    renderPage()

    expect(screen.getByRole('tab', { name: 'Atrasados' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Ranking' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Notas Finales' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Sin corregir' })).toBeInTheDocument()
  })

  it('muestra datos de atrasados en el tab activo', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    })
  })

  it('muestra botón de importar calificaciones', () => {
    renderPage()

    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument()
  })

  it('navega a importar cuando se hace clic en el botón', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByText('Importar calificaciones'))

    await waitFor(() => {
      expect(screen.getByText('Importar Page')).toBeInTheDocument()
    })
  })

  it('llama a configurarUmbral cuando se cambia el umbral', async () => {
    const user = userEvent.setup()
    renderPage()

    const numberInput = screen.getByRole('spinbutton')
    await user.clear(numberInput)
    await user.type(numberInput, '75')
    await user.tab()

    await waitFor(() => {
      expect(comisionesService.configurarUmbral).toHaveBeenCalled()
    })
  })

  it('muestra el ID de la comisión en el header', () => {
    renderPage('mat-test-123')

    expect(screen.getByText('ID: mat-test-123')).toBeInTheDocument()
  })
})
