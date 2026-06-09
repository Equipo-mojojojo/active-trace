/**
 * Tests for AuditoriaPage — TDD Strict
 *
 * Scenarios:
 * - Render de las 4 cards
 * - Aplicar filtros re-consulta (filters change triggers re-query)
 * - Gráfico de acciones por día visible con datos
 * - Estado vacío cuando no hay acciones
 * - Scope propio sin enviar actor_id
 * - Log completo de auditoría visible
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { AuditoriaPage } from './AuditoriaPage'

vi.mock('../hooks/useAuditoria', () => ({
  useAccionesPorDia: vi.fn(),
  useEstadoComunicaciones: vi.fn(),
  useInteracciones: vi.fn(),
  useUltimasAcciones: vi.fn(),
}))

import { useAccionesPorDia, useEstadoComunicaciones, useInteracciones, useUltimasAcciones } from '../hooks/useAuditoria'

const mockAcciones: import('../types/admin.types').AccionPorDia[] = [
  { fecha: '2024-06-01', total: 15 },
  { fecha: '2024-06-02', total: 8 },
]

const mockComunicaciones: import('../types/admin.types').EstadoComunicacionDocente[] = [
  { docente_id: 'd1', nombre_docente: 'Ana García', pendiente: 3, enviando: 1, enviado: 10, error: 0, cancelado: 2 },
]

const mockInteracciones: import('../types/admin.types').InteraccionDocente[] = [
  { docente_id: 'd1', nombre_docente: 'Ana García', materia_id: 'm1', nombre_materia: 'Matemática', accion: 'importar', total: 20 },
  { docente_id: 'd2', nombre_docente: 'Juan Pérez', materia_id: 'm2', nombre_materia: 'Física', accion: 'comunicar', total: 5 },
]

const mockUltimas: import('../types/admin.types').UltimaAccion[] = [
  { id: 'a1', timestamp: '2024-06-01T10:00:00', actor_id: 'd1', nombre_actor: 'Ana García', materia_id: 'm1', nombre_materia: 'Matemática', accion: 'importar', registros_afectados: 5, ip: '192.168.1.1', user_agent: 'Mozilla/5.0' },
]

function setupMocks() {
  vi.mocked(useAccionesPorDia).mockReturnValue({ data: mockAcciones, isLoading: false, isError: false } as ReturnType<typeof useAccionesPorDia>)
  vi.mocked(useEstadoComunicaciones).mockReturnValue({ data: mockComunicaciones, isLoading: false, isError: false } as ReturnType<typeof useEstadoComunicaciones>)
  vi.mocked(useInteracciones).mockReturnValue({ data: mockInteracciones, isLoading: false, isError: false } as ReturnType<typeof useInteracciones>)
  vi.mocked(useUltimasAcciones).mockReturnValue({ data: mockUltimas, isLoading: false, isError: false } as ReturnType<typeof useUltimasAcciones>)
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('AuditoriaPage — render de cards', () => {
  it('muestra las 4 cards de auditoría', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    expect(screen.getByLabelText('Acciones por día')).toBeInTheDocument()
    expect(screen.getByLabelText('Estado de comunicaciones')).toBeInTheDocument()
    expect(screen.getByLabelText('Interacciones por docente')).toBeInTheDocument()
    expect(screen.getByLabelText('Log completo de auditoría')).toBeInTheDocument()
  })

  it('muestra el gráfico con barras cuando hay datos', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    // Bars are rendered as divs with title
    expect(screen.getByTitle('2024-06-01: 15')).toBeInTheDocument()
    expect(screen.getByTitle('2024-06-02: 8')).toBeInTheDocument()
  })

  it('muestra el log completo con columnas correctas', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    expect(screen.getAllByText('Ana García').length).toBeGreaterThan(0)
    expect(screen.getAllByText('importar').length).toBeGreaterThan(0)
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument()
  })
})

describe('AuditoriaPage — estado vacío', () => {
  it('muestra estado vacío en acciones cuando no hay datos', () => {
    vi.mocked(useAccionesPorDia).mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useAccionesPorDia>)
    vi.mocked(useEstadoComunicaciones).mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useEstadoComunicaciones>)
    vi.mocked(useInteracciones).mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useInteracciones>)
    vi.mocked(useUltimasAcciones).mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useUltimasAcciones>)

    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('Sin actividad en el período seleccionado')).toBeInTheDocument()
  })
})

describe('AuditoriaPage — filtros re-consulta', () => {
  it('al cambiar el filtro desde re-llama a useAccionesPorDia con los filtros nuevos', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2024-06-01' } })

    expect(vi.mocked(useAccionesPorDia)).toHaveBeenCalledWith(expect.objectContaining({ desde: '2024-06-01' }))
  })
})

describe('AuditoriaPage — scope propio sin actor_id', () => {
  it('no envía actor_id en ninguna llamada de hook', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    // All hook calls must not include actor_id
    const allCalls = [
      ...vi.mocked(useAccionesPorDia).mock.calls,
      ...vi.mocked(useEstadoComunicaciones).mock.calls,
      ...vi.mocked(useInteracciones).mock.calls,
    ]
    allCalls.forEach((call) => {
      const filters = call[0]
      expect(filters).not.toHaveProperty('actor_id')
    })
  })
})

describe('AuditoriaPage — interacciones ordenadas', () => {
  it('muestra interacciones en orden descendente por total', () => {
    setupMocks()
    render(<AuditoriaPage />, { wrapper: makeWrapper() })

    const rows = screen.getAllByRole('row')
    // Ana García (total 20) should appear before Juan Pérez (total 5)
    const anaIndex = rows.findIndex((r) => r.textContent?.includes('Ana García'))
    const juanIndex = rows.findIndex((r) => r.textContent?.includes('Juan Pérez'))
    expect(anaIndex).toBeLessThan(juanIndex)
  })
})
