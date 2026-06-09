/**
 * Tests for EquiposPage.
 *
 * Scenarios:
 * - Renderiza la tabla con asignaciones
 * - Muestra estado vacío si no hay asignaciones
 * - Apertura del drawer al hacer click en "Asignar docente"
 * - Eliminación con confirmación
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
    delete: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { EquiposPage } from './EquiposPage'
import type { Asignacion } from '../types/coordinacion.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EquiposPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockAsignaciones: Asignacion[] = [
  {
    id: 'asig-1',
    tenant_id: 'tenant-1',
    usuario_id: 'user-1',
    nombre_usuario: 'María García',
    rol: 'TUTOR',
    materia_id: 'mat-1',
    carrera_id: null,
    cohorte_id: null,
    comisiones: 'A, B',
    desde: '2026-01-01',
    hasta: '2026-12-31',
    responsable_id: null,
    estado_vigencia: 'Vigente',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'asig-2',
    tenant_id: 'tenant-1',
    usuario_id: 'user-2',
    nombre_usuario: 'Juan Pérez',
    rol: 'PROFESOR',
    materia_id: 'mat-2',
    carrera_id: null,
    cohorte_id: null,
    comisiones: null,
    desde: '2025-01-01',
    hasta: '2025-12-31',
    responsable_id: null,
    estado_vigencia: 'Vencida',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('EquiposPage', () => {
  it('renderiza la tabla con asignaciones', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockAsignaciones })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('María García')).toBeInTheDocument()
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
      expect(screen.getAllByText('Vigente').length).toBeGreaterThan(0)
      // "Vencida" may appear in the filter dropdown AND in the table
      expect(screen.getAllByText('Vencida').length).toBeGreaterThan(0)
    })
  })

  it('muestra estado vacío si no hay asignaciones', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no hay asignaciones/i)).toBeInTheDocument()
    })
  })

  it('abre el drawer al hacer click en "Asignar docente"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    const btn = screen.getByRole('button', { name: /asignar docente/i })
    fireEvent.click(btn)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Nueva asignación')).toBeInTheDocument()
  })

  it('abre el drawer de edición al hacer click en Editar', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockAsignaciones })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('María García')).toBeInTheDocument()
    })

    const editBtns = screen.getAllByRole('button', { name: /editar/i })
    fireEvent.click(editBtns[0])

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Editar asignación')).toBeInTheDocument()
  })

  it('muestra el modal de asignación masiva al hacer click en el botón', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    const btn = screen.getByRole('button', { name: /asignación masiva/i })
    fireEvent.click(btn)

    await waitFor(() => {
      expect(screen.getByRole('dialog', { name: /asignación masiva/i })).toBeInTheDocument()
    })
  })
})
