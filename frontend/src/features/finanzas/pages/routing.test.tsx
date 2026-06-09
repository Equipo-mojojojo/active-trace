/**
 * Tests for C-24 routing — PermissionGuard and Sidebar visibility.
 *
 * Scenarios:
 * - Cada ruta de finanzas renderiza su page con el permiso correcto
 * - Redirección a /403 sin permiso
 * - Sidebar muestra/oculta secciones según permisos
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: vi.fn(() => ({ hasPermission: () => false })),
}))

import { usePermission } from '@/shared/hooks/usePermission'
import { PermissionGuard } from '@/shared/components/guards/PermissionGuard'
import { Sidebar } from '@/shared/components/layout/Sidebar'

function renderWithPermission(permission: string, userPermissions: string[]) {
  vi.mocked(usePermission).mockReturnValue({
    hasPermission: (p: string) => userPermissions.includes(p),
  })

  return render(
    <MemoryRouter initialEntries={['/test']}>
      <Routes>
        <Route path="/403" element={<div>Forbidden</div>} />
        <Route element={<PermissionGuard permission={permission} />}>
          <Route path="/test" element={<div>Protected Content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => { vi.clearAllMocks() })
afterEach(() => { vi.restoreAllMocks() })

describe('PermissionGuard — C-24 rutas finanzas', () => {
  it('redirige a /403 sin liquidaciones:ver', async () => {
    renderWithPermission('liquidaciones:ver', ['atrasados:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })

  it('renderiza contenido con liquidaciones:ver', async () => {
    renderWithPermission('liquidaciones:ver', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  it('redirige a /403 sin liquidaciones:configurar-salarios', async () => {
    renderWithPermission('liquidaciones:configurar-salarios', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })

  it('redirige a /403 sin facturas:ver', async () => {
    renderWithPermission('facturas:ver', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })
})

describe('PermissionGuard — C-24 rutas admin', () => {
  it('redirige a /403 sin estructura:gestionar', async () => {
    renderWithPermission('estructura:gestionar', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })

  it('renderiza contenido con estructura:gestionar', async () => {
    renderWithPermission('estructura:gestionar', ['estructura:gestionar'])
    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  it('redirige a /403 sin usuarios:gestionar', async () => {
    renderWithPermission('usuarios:gestionar', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })

  it('redirige a /403 sin auditoria:ver', async () => {
    renderWithPermission('auditoria:ver', ['liquidaciones:ver'])
    await waitFor(() => {
      expect(screen.getByText('Forbidden')).toBeInTheDocument()
    })
  })
})

describe('Sidebar — visibilidad secciones C-24', () => {
  it('no muestra sección Finanzas para PROFESOR sin liquidaciones:ver', () => {
    vi.mocked(usePermission).mockReturnValue({
      hasPermission: (p: string) => p === '' || p === 'atrasados:ver',
    })
    render(<MemoryRouter><Sidebar /></MemoryRouter>)

    expect(screen.queryByText('Liquidaciones')).not.toBeInTheDocument()
    expect(screen.queryByText('Grilla salarial')).not.toBeInTheDocument()
    expect(screen.queryByText('Facturas')).not.toBeInTheDocument()
  })

  it('muestra sección Finanzas para usuario con liquidaciones:ver', () => {
    vi.mocked(usePermission).mockReturnValue({
      hasPermission: (p: string) => ['liquidaciones:ver', 'facturas:ver'].includes(p) || p === '',
    })
    render(<MemoryRouter><Sidebar /></MemoryRouter>)

    expect(screen.getByText('Liquidaciones')).toBeInTheDocument()
    expect(screen.getByText('Facturas')).toBeInTheDocument()
  })

  it('muestra sección Administración para ADMIN con todos los permisos', () => {
    vi.mocked(usePermission).mockReturnValue({ hasPermission: () => true })
    render(<MemoryRouter><Sidebar /></MemoryRouter>)

    expect(screen.getByText('Estructura Académica')).toBeInTheDocument()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Auditoría')).toBeInTheDocument()
  })

  it('FINANZAS no ve sección Administración sin estructura:gestionar', () => {
    vi.mocked(usePermission).mockReturnValue({
      hasPermission: (p: string) => ['liquidaciones:ver', 'facturas:ver', ''].includes(p),
    })
    render(<MemoryRouter><Sidebar /></MemoryRouter>)

    expect(screen.queryByText('Estructura Académica')).not.toBeInTheDocument()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
  })
})
