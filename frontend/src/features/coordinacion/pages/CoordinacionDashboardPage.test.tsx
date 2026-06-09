/**
 * Tests for CoordinacionDashboardPage.
 *
 * Scenarios:
 * - Renderiza las 4 cards de acceso rápido
 * - Muestra tareas pendientes con badge de estado
 * - Muestra avisos activos con badge de severidad
 * - Muestra estado vacío si no hay tareas
 * - Muestra estado vacío si no hay avisos
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
import { CoordinacionDashboardPage } from './CoordinacionDashboardPage'
import type { Tarea, Aviso } from '../types/coordinacion.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <CoordinacionDashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockTareas: Tarea[] = [
  {
    id: 'tarea-1',
    materia_id: null,
    asignado_a: 'user-1',
    asignado_por: 'user-2',
    estado: 'Pendiente',
    descripcion: 'Revisar planillas de calificaciones',
    contexto_id: null,
  },
  {
    id: 'tarea-2',
    materia_id: null,
    asignado_a: 'user-1',
    asignado_por: 'user-2',
    estado: 'En progreso',
    descripcion: 'Coordinar reunión con docentes',
    contexto_id: null,
  },
]

const mockAvisos: Aviso[] = [
  {
    id: 'aviso-1',
    alcance: 'Global',
    materia_id: null,
    cohorte_id: null,
    rol_destino: null,
    severidad: 'Info',
    titulo: 'Actualización del sistema',
    cuerpo: 'Se realizará mantenimiento el viernes.',
    inicio_en: '2026-06-01T00:00:00Z',
    fin_en: null,
    orden: 0,
    activo: true,
    requiere_ack: false,
  },
  {
    id: 'aviso-2',
    alcance: 'Global',
    materia_id: null,
    cohorte_id: null,
    rol_destino: null,
    severidad: 'Crítico',
    titulo: 'Cierre de notas urgente',
    cuerpo: 'Plazo vence esta semana.',
    inicio_en: '2026-06-01T00:00:00Z',
    fin_en: null,
    orden: 1,
    activo: true,
    requiere_ack: true,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CoordinacionDashboardPage', () => {
  it('renderiza las 4 cards de acceso rápido', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Equipos Docentes')).toBeInTheDocument()
      expect(screen.getByText('Avisos')).toBeInTheDocument()
      expect(screen.getByText('Tareas')).toBeInTheDocument()
      expect(screen.getByText('Monitor Institucional')).toBeInTheDocument()
    })
  })

  it('muestra tareas pendientes con badges de estado', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: mockTareas }) // tareas/mias
      .mockResolvedValueOnce({ data: [] }) // avisos

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Revisar planillas de calificaciones')).toBeInTheDocument()
      expect(screen.getByText('Coordinar reunión con docentes')).toBeInTheDocument()
      expect(screen.getByText('Pendiente')).toBeInTheDocument()
      expect(screen.getByText('En progreso')).toBeInTheDocument()
    })
  })

  it('muestra avisos activos con badges de severidad', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: [] }) // tareas
      .mockResolvedValueOnce({ data: mockAvisos }) // avisos

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Actualización del sistema')).toBeInTheDocument()
      expect(screen.getByText('Cierre de notas urgente')).toBeInTheDocument()
      expect(screen.getByText('Info')).toBeInTheDocument()
      expect(screen.getByText('Crítico')).toBeInTheDocument()
    })
  })

  it('muestra estado vacío cuando no hay tareas pendientes', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: [] }) // tareas
      .mockResolvedValueOnce({ data: [] }) // avisos

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no tenés tareas pendientes/i)).toBeInTheDocument()
    })
  })

  it('excluye tareas resueltas y canceladas de la sección pendientes', async () => {
    const tareasResueltas: Tarea[] = [
      { ...mockTareas[0], estado: 'Resuelta' },
      { ...mockTareas[1], estado: 'Cancelada' },
    ]
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: tareasResueltas })
      .mockResolvedValueOnce({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no tenés tareas pendientes/i)).toBeInTheDocument()
    })
    expect(screen.queryByText('Revisar planillas de calificaciones')).not.toBeInTheDocument()
  })
})
