/**
 * Tests for AppLayout.
 * TDD: RED first.
 *
 * Scenarios:
 * - Render: shows user name and tenant name in the header
 * - Logout: click on logout button calls authService.logout and clears session
 * - Fail-safe logout: even if backend fails, session is cleared
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

// Mock the authService
vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    logout: vi.fn(),
  },
}))

// Mock Sidebar to keep tests focused on AppLayout
vi.mock('./Sidebar', () => ({
  Sidebar: () => <aside data-testid="sidebar">Sidebar</aside>,
}))

import { authService } from '@/features/auth/services/authService'

function makeAuthContext(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
    roles: ['PROFESOR'],
    permissions: ['alumnos:ver'],
    tenant: { id: 't1', nombre: 'USAL' },
    isAuthenticated: true,
    setSession: () => undefined,
    clearSession: vi.fn(),
    ...overrides,
  }
}

function renderAppLayout(ctx: AuthContextValue) {
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<AppLayoutLazy />}>
            <Route index element={<div>Dashboard Content</div>} />
          </Route>
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

let AppLayoutLazy: React.ComponentType
beforeEach(async () => {
  const mod = await import('./AppLayout')
  AppLayoutLazy = mod.AppLayout
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('AppLayout', () => {
  describe('Render', () => {
    it('shows the user name in the header', () => {
      const ctx = makeAuthContext()
      renderAppLayout(ctx)

      expect(screen.getByLabelText(/nombre del usuario/i)).toHaveTextContent('Test User')
    })

    it('shows the tenant name in the header', () => {
      const ctx = makeAuthContext()
      renderAppLayout(ctx)

      expect(screen.getByText('USAL')).toBeInTheDocument()
    })

    it('renders the sidebar', () => {
      const ctx = makeAuthContext()
      renderAppLayout(ctx)

      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })
  })

  describe('Logout', () => {
    it('calls authService.logout and clearSession when logout button is clicked', async () => {
      const user = userEvent.setup()
      const clearSession = vi.fn()
      vi.mocked(authService.logout).mockResolvedValueOnce(undefined)

      const ctx = makeAuthContext({ clearSession })
      renderAppLayout(ctx)

      await user.click(screen.getByRole('button', { name: /cerrar sesión/i }))

      await waitFor(() => {
        expect(authService.logout).toHaveBeenCalledOnce()
        expect(clearSession).toHaveBeenCalledOnce()
      })
    })

    it('redirects to /login after logout', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.logout).mockResolvedValueOnce(undefined)

      const ctx = makeAuthContext()
      renderAppLayout(ctx)

      await user.click(screen.getByRole('button', { name: /cerrar sesión/i }))

      await waitFor(() => {
        expect(screen.getByText(/login page/i)).toBeInTheDocument()
      })
    })

    it('TRIANGULATE — clears session even when backend logout fails (fail-safe)', async () => {
      const user = userEvent.setup()
      const clearSession = vi.fn()
      vi.mocked(authService.logout).mockRejectedValueOnce(new Error('Backend error'))

      const ctx = makeAuthContext({ clearSession })
      renderAppLayout(ctx)

      await user.click(screen.getByRole('button', { name: /cerrar sesión/i }))

      // Even with backend failure, session must be cleared
      await waitFor(() => {
        expect(clearSession).toHaveBeenCalledOnce()
      })
    })
  })
})
