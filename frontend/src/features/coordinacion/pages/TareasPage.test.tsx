/**
 * Tests for TareasPage.
 *
 * Scenarios:
 * - Renderiza los tabs
 * - Cambio de tab actualiza query param en URL
 * - Muestra tareas en la tabla
 * - Estado vacío cuando no hay tareas
 * - Abre modal de nueva tarea
 * - Abre drawer de detalle al hacer click en "Ver detalle"
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
import { TareasPage } from './TareasPage'
import type { Tarea } from '../types/coordinacion.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage(initialSearch = '') {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/coordinacion/tareas${initialSearch}`]}>
        <TareasPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockTareas: Tarea[] = [
  {
    id: 'tarea-1',
    materia_id: null,
    asignado_a: 'aaaaaaaa-0000-0000-0000-000000000001',
    asignado_por: 'bbbbbbbb-0000-0000-0000-000000000002',
    estado: 'Pendiente',
    descripcion: 'Revisar actas del coloquio',
    contexto_id: null,
  },
  {
    id: 'tarea-2',
    materia_id: null,
    asignado_a: 'aaaaaaaa-0000-0000-0000-000000000001',
    asignado_por: 'bbbbbbbb-0000-0000-0000-000000000002',
    estado: 'En progreso',
    descripcion: 'Coordinar reunión semanal',
    contexto_id: null,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('TareasPage', () => {
  it('renderiza los tres tabs', () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    expect(screen.getByRole('button', { name: /mis tareas/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /asignadas por mí/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /todas/i })).toBeInTheDocument()
  })

  it('renderiza tareas en la tabla', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: mockTareas })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Revisar actas del coloquio')).toBeInTheDocument()
      expect(screen.getByText('Coordinar reunión semanal')).toBeInTheDocument()
    })
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
    expect(screen.getByText('En progreso')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay tareas', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no tenés tareas en este momento/i)).toBeInTheDocument()
    })
  })

  it('abre modal "Nueva tarea" al hacer click en el botón', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /nueva tarea/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /nueva tarea/i })).toBeInTheDocument()
    })
  })

  it('abre el drawer de detalle al hacer click en "Ver detalle"', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: mockTareas })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Revisar actas del coloquio')).toBeInTheDocument()
    })

    // mock comentarios fetch
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    const btns = screen.getAllByRole('button', { name: /ver detalle/i })
    fireEvent.click(btns[0])

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /detalle de tarea/i })).toBeInTheDocument()
    })
  })

  it('cambia de tab al hacer click', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    const tabTodas = screen.getByRole('button', { name: /todas/i })
    fireEvent.click(tabTodas)

    await waitFor(() => {
      expect(tabTodas.className).toContain('text-indigo-600')
    })
  })
})
