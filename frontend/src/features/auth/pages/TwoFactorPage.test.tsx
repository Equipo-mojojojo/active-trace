/**
 * Tests for TwoFactorPage.
 * TDD: RED first.
 *
 * Scenarios:
 * 9.3a - Render: shows 6-digit code field and verify button
 * 9.3b - Redirect: if no session_token in sessionStorage → redirects to /login
 * 9.3c - Error: invalid code → shows error message
 * 9.3d - Success: valid code → calls setSession and removes the session token
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    verifyTwoFactor: vi.fn(),
    refresh: vi.fn().mockRejectedValue(new Error('no session')),
  },
}))

import { authService } from '@/features/auth/services/authService'
import type { AuthResponse } from '../types'

// Use AuthContext.Provider directly to avoid the AuthProvider's restore-session effect
function makeAuthContext(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user: null,
    roles: [],
    permissions: [],
    tenant: null,
    isAuthenticated: false,
    setSession: vi.fn(),
    clearSession: vi.fn(),
    ...overrides,
  }
}

function renderTwoFactorPage(ctx?: AuthContextValue) {
  const authCtx = ctx ?? makeAuthContext()
  return render(
    <AuthContext.Provider value={authCtx}>
      <MemoryRouter initialEntries={['/auth/2fa']}>
        <Routes>
          <Route path="/auth/2fa" element={<TwoFactorPageLazy />} />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

let TwoFactorPageLazy: React.ComponentType
beforeEach(async () => {
  const mod = await import('./TwoFactorPage')
  TwoFactorPageLazy = mod.TwoFactorPage
  // By default, set the session token so the page doesn't redirect
  sessionStorage.setItem('2fa_session_token', 'partial-session-xyz')
})

afterEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
})

describe('TwoFactorPage', () => {
  describe('Render', () => {
    it('shows the 6-digit code field and verify button', () => {
      renderTwoFactorPage()

      expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /verificar/i })).toBeInTheDocument()
    })
  })

  describe('Redirect when no session token', () => {
    it('redirects to /login when 2fa_session_token is not in sessionStorage', async () => {
      sessionStorage.removeItem('2fa_session_token')

      renderTwoFactorPage()

      await waitFor(() => {
        expect(screen.getByText(/login page/i)).toBeInTheDocument()
      })
      expect(screen.queryByRole('button', { name: /verificar/i })).not.toBeInTheDocument()
    })
  })

  describe('Error: invalid code', () => {
    it('shows "Código inválido o expirado" when backend rejects the code', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.verifyTwoFactor).mockRejectedValueOnce(
        new Error('Invalid TOTP code'),
      )

      renderTwoFactorPage()

      await user.type(screen.getByLabelText(/código totp/i), '999999')
      await user.click(screen.getByRole('button', { name: /verificar/i }))

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/código inválido o expirado/i)
      })
    })
  })

  describe('Success: valid code', () => {
    it('calls setSession with the auth response after successful verification', async () => {
      const user = userEvent.setup()
      const setSession = vi.fn()
      const mockResponse: AuthResponse = {
        user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
        access_token: 'token-abc',
        permissions: ['alumnos:ver'],
        roles: ['PROFESOR'],
        tenant: { id: 't1', nombre: 'USAL' },
      }
      vi.mocked(authService.verifyTwoFactor).mockResolvedValueOnce(mockResponse)

      renderTwoFactorPage(makeAuthContext({ setSession }))

      await user.type(screen.getByLabelText(/código totp/i), '123456')
      await user.click(screen.getByRole('button', { name: /verificar/i }))

      await waitFor(() => {
        expect(setSession).toHaveBeenCalledWith(
          mockResponse.user,
          mockResponse.roles,
          mockResponse.permissions,
          mockResponse.tenant,
          mockResponse.access_token,
        )
      })
    })

    it('removes the session token from sessionStorage on success', async () => {
      const user = userEvent.setup()
      const mockResponse: AuthResponse = {
        user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
        access_token: 'token-abc',
        permissions: ['alumnos:ver'],
        roles: ['PROFESOR'],
        tenant: { id: 't1', nombre: 'USAL' },
      }
      vi.mocked(authService.verifyTwoFactor).mockResolvedValueOnce(mockResponse)

      renderTwoFactorPage()

      await user.type(screen.getByLabelText(/código totp/i), '123456')
      await user.click(screen.getByRole('button', { name: /verificar/i }))

      await waitFor(() => {
        expect(sessionStorage.getItem('2fa_session_token')).toBeNull()
      })
    })
  })
})
