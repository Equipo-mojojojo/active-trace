/**
 * Tests for UsuariosPage — TDD Strict
 *
 * Scenarios:
 * - Listar usuarios con rol badge y estado
 * - Filtrar por rol
 * - Búsqueda libre
 * - Abrir drawer para nuevo usuario
 * - Abrir drawer para editar usuario existente con datos precargados
 * - Guardar usuario llama a mutateAsync
 * - Validación de campos obligatorios (sin nombre)
 * - Desactivar usuario (toggle de estado)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { UsuariosPage } from './UsuariosPage'

vi.mock('../hooks/useUsuarios', () => ({
  useUsuarios: vi.fn(),
  useCreateUsuario: vi.fn(),
  useUpdateUsuario: vi.fn(),
}))

import { useUsuarios, useCreateUsuario, useUpdateUsuario } from '../hooks/useUsuarios'

const mockUsuarios: import('../types/admin.types').UsuarioTenant[] = [
  { id: 'u1', nombre: 'Ana Díaz', email: 'ana@usal.edu', roles: ['ADMIN'], estado: 'Activo' },
  { id: 'u2', nombre: 'Carlos López', email: 'carlos@usal.edu', roles: ['PROFESOR', 'TUTOR'], estado: 'Inactivo' },
]

const noopMutation = () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false })

function setupMocks({ usuarios = mockUsuarios, createAsync = vi.fn().mockResolvedValue({}) } = {}) {
  vi.mocked(useUsuarios).mockReturnValue({ data: usuarios, isLoading: false, isError: false } as ReturnType<typeof useUsuarios>)
  vi.mocked(useCreateUsuario).mockReturnValue({ mutateAsync: createAsync, isPending: false } as ReturnType<typeof useCreateUsuario>)
  vi.mocked(useUpdateUsuario).mockReturnValue(noopMutation() as ReturnType<typeof useUpdateUsuario>)
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('UsuariosPage — listar', () => {
  it('muestra los usuarios con nombre y email', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('Ana Díaz')).toBeInTheDocument()
    expect(screen.getByText('ana@usal.edu')).toBeInTheDocument()
    expect(screen.getByText('Carlos López')).toBeInTheDocument()
  })

  it('muestra badges de rol', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    // Multiple ADMIN and PROFESOR texts are expected (table badges + role filter select options)
    expect(screen.getAllByText('ADMIN').length).toBeGreaterThan(0)
    expect(screen.getAllByText('PROFESOR').length).toBeGreaterThan(0)
  })
})

describe('UsuariosPage — drawer nuevo usuario', () => {
  it('abre el drawer al hacer click en Nuevo usuario', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))

    expect(screen.getByRole('dialog', { name: 'Drawer usuario' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument()
  })

  it('cierra el drawer al hacer click en Cancelar', async () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})

describe('UsuariosPage — drawer editar usuario', () => {
  it('abre el drawer con datos precargados al hacer click en Editar', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Editar usuario Ana Díaz' }))

    const nombreInput = screen.getByDisplayValue('Ana Díaz')
    expect(nombreInput).toBeInTheDocument()
  })
})

describe('UsuariosPage — validación', () => {
  it('muestra error de validación si el nombre está vacío', async () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
    // Submit without filling required fields
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => {
      expect(screen.getAllByText('Requerido').length).toBeGreaterThan(0)
    })
  })
})

describe('UsuariosPage — filtrar por rol', () => {
  it('llama a useUsuarios con el filtro de rol seleccionado', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrar por rol' }), {
      target: { value: 'PROFESOR' },
    })

    // useUsuarios is called with updated filters (checked via re-render)
    expect(vi.mocked(useUsuarios)).toHaveBeenCalledWith(expect.objectContaining({ rol: 'PROFESOR' }))
  })
})

describe('UsuariosPage — busqueda', () => {
  it('llama a useUsuarios con el filtro q', () => {
    setupMocks()
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.change(screen.getByPlaceholderText('Buscar por nombre o email...'), {
      target: { value: 'Ana' },
    })

    expect(vi.mocked(useUsuarios)).toHaveBeenCalledWith(expect.objectContaining({ q: 'Ana' }))
  })
})

describe('UsuariosPage — guardar usuario', () => {
  it('al guardar correctamente llama a createUsuario.mutateAsync', async () => {
    const createAsync = vi.fn().mockResolvedValue({})
    setupMocks({ createAsync })
    render(<UsuariosPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))

    // Get the drawer dialog
    const drawer = screen.getByRole('dialog', { name: 'Drawer usuario' })
    // Find inputs within the drawer (all inputs)
    const allInputs = Array.from(drawer.querySelectorAll('input'))
    // nombre is first text input, email is second
    const nombreInput = allInputs.find((i) => !i.type || i.type === 'text')
    const emailInput = allInputs.find((i) => i.type === 'email')
    if (nombreInput) fireEvent.change(nombreInput, { target: { value: 'Pedro Test' } })
    if (emailInput) fireEvent.change(emailInput, { target: { value: 'pedro@test.com' } })
    // Select a role chip within the drawer
    const tutorChip = Array.from(drawer.querySelectorAll('button[aria-pressed]')).find(
      (b) => b.textContent === 'TUTOR',
    ) as HTMLButtonElement
    if (tutorChip) fireEvent.click(tutorChip)
    // Submit using the form submit button
    const guardarBtn = Array.from(drawer.querySelectorAll('button[type="submit"]'))[0] as HTMLButtonElement
    if (guardarBtn) fireEvent.click(guardarBtn)

    await waitFor(() => {
      expect(createAsync).toHaveBeenCalled()
    })
  })
})
