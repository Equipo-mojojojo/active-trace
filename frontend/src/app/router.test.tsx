/**
 * Tests for C-23 routing — PermissionGuard and Sidebar visibility.
 *
 * Scenarios:
 * - PermissionGuard redirige a /403 cuando falta el permiso
 * - PermissionGuard permite acceso con el permiso correcto
 * - Sidebar no muestra items de Coordinación para PROFESOR
 * - Sidebar muestra items de Coordinación para COORDINADOR
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

// Mock usePermission so Sidebar doesn't need AuthProvider chain
vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: vi.fn(() => ({ hasPermission: () => false })),
}))

import { usePermission } from '@/shared/hooks/usePermission'
import { PermissionGuard } from '@/shared/components/guards/PermissionGuard'
import { Sidebar } from '@/shared/components/layout/Sidebar'

function makeAuthContext(permissions: string[]): AuthContextValue {
  return {
    user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
    roles: ['COORDINADOR'],
    permissions,
    tenant: { id: 't1', nombre: 'USAL' },
    isAuthenticated: true,
    setSession: () => undefined,
    clearSession: vi.fn(),
  }
}

function renderWithPermission(permission: string, userPermissions: string[]) {
  // Configure the usePermission mock to check the userPermissions list
  vi.mocked(usePermission).mockReturnValue({
    hasPermission: (p: string) => userPermissions.includes(p),
  })

  return render(
    <AuthContext.Provider value={makeAuthContext(userPermissions)}>
      <MemoryRouter initialEntries={['/test']}>
        <Routes>
          <Route path="/403" element={<div>Forbidden</div>} />
          <Route element={<PermissionGuard permission={permission} />}>
            <Route path="/test" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('PermissionGuard — C-23 routes', () => {
  it('redirige a /403 cuando el usuario NO tiene el permiso equipos:asignar', async () => {
    renderWithPermission('equipos:asignar', ['atrasados:ver'])

    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renderiza el contenido protegido cuando el usuario tiene el permiso equipos:asignar', async () => {
    renderWithPermission('equipos:asignar', ['equipos:asignar'])

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
    expect(screen.queryByText('Forbidden')).not.toBeInTheDocument()
  })

  it('redirige a /403 para encuentros:gestionar sin el permiso', async () => {
    renderWithPermission('encuentros:gestionar', ['equipos:asignar'])

    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })

  it('permite acceso con encuentros:gestionar cuando tiene el permiso', async () => {
    renderWithPermission('encuentros:gestionar', ['encuentros:gestionar'])

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  it('redirige a /403 para avisos:publicar sin el permiso', async () => {
    renderWithPermission('avisos:publicar', ['atrasados:ver'])

    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })
})

describe('Sidebar — visibilidad de items C-23', () => {
  it('no muestra items de Coordinación para PROFESOR sin equipos:asignar', () => {
    vi.mocked(usePermission).mockReturnValue({
      hasPermission: (p: string) => p === '' || p === 'atrasados:ver',
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.queryByText('Equipos Docentes')).not.toBeInTheDocument()
    expect(screen.queryByText('Coloquios')).not.toBeInTheDocument()
  })

  it('muestra items de Coordinación para COORDINADOR con equipos:asignar', () => {
    vi.mocked(usePermission).mockReturnValue({
      hasPermission: () => true, // COORDINADOR has all permissions
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByText('Equipos Docentes')).toBeInTheDocument()
    expect(screen.getByText('Coloquios')).toBeInTheDocument()
    expect(screen.getByText('Encuentros')).toBeInTheDocument()
  })
})
