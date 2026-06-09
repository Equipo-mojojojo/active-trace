/**
 * Tests for EstructuraAcademicaPage — TDD Strict
 *
 * Scenarios:
 * - Render de los tres tabs
 * - Crear carrera inline
 * - 409 código duplicado muestra error inline
 * - Soft delete carrera
 * - grupo_plus_clave en materia
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { EstructuraAcademicaPage } from './EstructuraAcademicaPage'

vi.mock('../hooks/useEstructura', () => ({
  useCarreras: vi.fn(),
  useCreateCarrera: vi.fn(),
  useUpdateCarrera: vi.fn(),
  useDeleteCarrera: vi.fn(),
  useCohortes: vi.fn(),
  useCreateCohorte: vi.fn(),
  useUpdateCohorte: vi.fn(),
  useDeleteCohorte: vi.fn(),
  useMaterias: vi.fn(),
  useCreateMateria: vi.fn(),
  useUpdateMateria: vi.fn(),
  useDeleteMateria: vi.fn(),
}))

import {
  useCarreras, useCreateCarrera, useUpdateCarrera, useDeleteCarrera,
  useCohortes, useCreateCohorte, useUpdateCohorte, useDeleteCohorte,
  useMaterias, useCreateMateria, useUpdateMateria, useDeleteMateria,
} from '../hooks/useEstructura'

const mockCarreras: import('../types/admin.types').Carrera[] = [
  { id: 'c1', codigo: 'ING', nombre: 'Ingeniería', estado: 'Activa' },
  { id: 'c2', codigo: 'MED', nombre: 'Medicina', estado: 'Inactiva' },
]

const mockMaterias: import('../types/admin.types').Materia[] = [
  { id: 'm1', codigo: 'MAT1', nombre: 'Matemática', estado: 'Activa', grupo_plus_clave: 'PROG' },
]

const noopMutation = () => ({ mutateAsync: vi.fn(), isPending: false })

function setupMocks(opts: { createAsync?: () => Promise<unknown> } = {}) {
  vi.mocked(useCarreras).mockReturnValue({ data: mockCarreras, isLoading: false, isError: false } as ReturnType<typeof useCarreras>)
  vi.mocked(useCreateCarrera).mockReturnValue({ mutateAsync: opts.createAsync ?? vi.fn().mockResolvedValue({}), isPending: false } as ReturnType<typeof useCreateCarrera>)
  vi.mocked(useUpdateCarrera).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateCarrera>)
  vi.mocked(useDeleteCarrera).mockReturnValue(noopMutation() as ReturnType<typeof useDeleteCarrera>)

  vi.mocked(useCohortes).mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useCohortes>)
  vi.mocked(useCreateCohorte).mockReturnValue(noopMutation() as ReturnType<typeof useCreateCohorte>)
  vi.mocked(useUpdateCohorte).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateCohorte>)
  vi.mocked(useDeleteCohorte).mockReturnValue(noopMutation() as ReturnType<typeof useDeleteCohorte>)

  vi.mocked(useMaterias).mockReturnValue({ data: mockMaterias, isLoading: false, isError: false } as ReturnType<typeof useMaterias>)
  vi.mocked(useCreateMateria).mockReturnValue(noopMutation() as ReturnType<typeof useCreateMateria>)
  vi.mocked(useUpdateMateria).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateMateria>)
  vi.mocked(useDeleteMateria).mockReturnValue(noopMutation() as ReturnType<typeof useDeleteMateria>)
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('EstructuraAcademicaPage — tabs', () => {
  it('muestra los tres tabs: Carreras, Cohortes, Materias', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    expect(screen.getByRole('tab', { name: 'Carreras' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Cohortes' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Materias' })).toBeInTheDocument()
  })

  it('el tab Carreras está activo por defecto y muestra los datos', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('ING')).toBeInTheDocument()
    expect(screen.getByText('Ingeniería')).toBeInTheDocument()
  })

  it('al hacer click en Materias muestra datos de materias', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('tab', { name: 'Materias' }))

    expect(screen.getByText('MAT1')).toBeInTheDocument()
    expect(screen.getByText('PROG')).toBeInTheDocument()
  })
})

describe('EstructuraAcademicaPage — crear carrera', () => {
  it('al hacer click en Nueva carrera muestra fila de edición', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva carrera' }))

    expect(screen.getByPlaceholderText('Código')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Nombre')).toBeInTheDocument()
  })

  it('al guardar nueva carrera llama a createCarrera.mutateAsync', async () => {
    const createAsync = vi.fn().mockResolvedValue({})
    setupMocks({ createAsync })
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva carrera' }))
    fireEvent.click(screen.getAllByRole('button', { name: 'Guardar' })[0])

    await waitFor(() => {
      expect(createAsync).toHaveBeenCalled()
    })
  })
})

describe('EstructuraAcademicaPage — 409 duplicado', () => {
  it('muestra error inline cuando el backend responde 409', async () => {
    const error409 = Object.assign(new Error('409'), { response: { status: 409 } })
    const createAsync = vi.fn().mockRejectedValue(error409)
    setupMocks({ createAsync })
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva carrera' }))
    fireEvent.click(screen.getAllByRole('button', { name: 'Guardar' })[0])

    await waitFor(() => {
      expect(screen.getByText(/duplicado/i)).toBeInTheDocument()
    })
  })
})

describe('EstructuraAcademicaPage — estado badges', () => {
  it('muestra badge Activa verde e Inactiva gris', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    const activa = screen.getByText('Activa')
    const inactiva = screen.getByText('Inactiva')

    expect(activa.className).toContain('green')
    expect(inactiva.className).toContain('slate')
  })
})

describe('EstructuraAcademicaPage — grupo_plus_clave', () => {
  it('muestra grupo_plus_clave en materias', () => {
    setupMocks()
    render(<EstructuraAcademicaPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('tab', { name: 'Materias' }))

    expect(screen.getByText('PROG')).toBeInTheDocument()
  })
})
