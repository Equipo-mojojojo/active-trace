import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
import { TabsComision } from './TabsComision'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderComponent(props = {}) {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <TabsComision materiaId="mat-1" {...props} />
    </QueryClientProvider>,
  )
}

const mockAtrasados = {
  total: 2,
  atrasados: [
    {
      entrada_padron_id: 'ep-1',
      nombre: 'Juan',
      apellidos: 'Perez',
      comision: 'A',
      materia_id: 'mat-1',
      actividades_faltantes: ['TP1'],
      actividades_reprobadas: [],
    },
  ],
}

const mockRanking = {
  total: 1,
  ranking: [
    { entrada_padron_id: 'ep-2', nombre: 'Ana', apellidos: 'Lopez', comision: 'A', aprobadas: 8 },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(comisionesService.getAtrasados).mockResolvedValue(mockAtrasados)
  vi.mocked(comisionesService.getRanking).mockResolvedValue(mockRanking)
  vi.mocked(comisionesService.getNotasFinales).mockResolvedValue({
    actividades_seleccionadas: [],
    notas: [],
  })
})

describe('TabsComision', () => {
  it('renderiza los 4 tabs de análisis', () => {
    renderComponent()

    expect(screen.getByRole('tab', { name: 'Atrasados' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Ranking' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Notas Finales' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Sin corregir' })).toBeInTheDocument()
  })

  it('muestra datos de atrasados en el tab activo por defecto', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    })
  })

  it('cambia al tab de Ranking al hacer clic', async () => {
    const user = userEvent.setup()
    renderComponent()

    await user.click(screen.getByRole('tab', { name: 'Ranking' }))

    await waitFor(() => {
      expect(screen.getByText('Lopez, Ana')).toBeInTheDocument()
    })
  })

  it('muestra panel de Sin corregir al hacer clic', async () => {
    const user = userEvent.setup()
    renderComponent()

    await user.click(screen.getByRole('tab', { name: 'Sin corregir' }))

    await waitFor(() => {
      expect(screen.getByText(/entregas pendientes/i)).toBeInTheDocument()
    })
  })

  it('muestra notas finales al hacer clic en el tab', async () => {
    const user = userEvent.setup()
    renderComponent()

    await user.click(screen.getByRole('tab', { name: 'Notas Finales' }))

    await waitFor(() => {
      expect(screen.getByText(/no hay notas finales/i)).toBeInTheDocument()
    })
  })

  it('llama al callback onComunicar cuando se seleccionan alumnos y se clickea comunicar', async () => {
    const user = userEvent.setup()
    const onComunicar = vi.fn()

    renderComponent({ onComunicar })

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    })

    // Select the alumno
    const checkbox = screen.getAllByRole('checkbox')[0]
    await user.click(checkbox)

    // The "comunicar seleccionados" button should appear
    await waitFor(() => {
      expect(screen.getByText(/comunicar seleccionados/i)).toBeInTheDocument()
    })

    await user.click(screen.getByText(/comunicar seleccionados/i))
    expect(onComunicar).toHaveBeenCalled()
  })
})
