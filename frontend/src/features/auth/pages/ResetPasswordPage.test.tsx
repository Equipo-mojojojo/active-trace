/**
 * Tests for ResetPasswordPage.
 * TDD: RED first.
 *
 * Scenarios:
 * - Render with valid token in URL: shows password and confirm fields
 * - No token in URL: shows invalid-token message immediately
 * - Submit success: calls authService.resetPassword and shows success message
 * - Success then redirect: timer fires → navigates to /login
 * - Backend error (token expired): shows invalid-token message
 * - TRIANGULATE: password mismatch validation
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    resetPassword: vi.fn(),
    refresh: vi.fn().mockRejectedValue(new Error('no session')),
  },
}))

import { authService } from '@/features/auth/services/authService'

// Use AuthContext.Provider directly to avoid AuthProvider's restore-session effect
function makeAuthContext(): AuthContextValue {
  return {
    user: null,
    roles: [],
    permissions: [],
    tenant: null,
    isAuthenticated: false,
    setSession: vi.fn(),
    clearSession: vi.fn(),
  }
}

function renderResetPasswordPage(initialPath = '/auth/reset-password?token=valid-token-123') {
  const ctx = makeAuthContext()
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/auth/reset-password" element={<ResetPasswordPageLazy />} />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

let ResetPasswordPageLazy: React.ComponentType
beforeEach(async () => {
  const mod = await import('./ResetPasswordPage')
  ResetPasswordPageLazy = mod.ResetPasswordPage
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('ResetPasswordPage', () => {
  describe('Render with valid token', () => {
    it('shows new password and confirm password fields when token is in URL', () => {
      renderResetPasswordPage('/auth/reset-password?token=valid-token-123')

      expect(screen.getByLabelText(/nueva contraseña/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /restablecer contraseña/i }),
      ).toBeInTheDocument()
    })
  })

  describe('No token in URL', () => {
    it('shows invalid-token message when there is no token query param', () => {
      renderResetPasswordPage('/auth/reset-password')

      expect(
        screen.getByText(/el enlace expiró o ya fue usado/i),
      ).toBeInTheDocument()
      expect(
        screen.queryByRole('button', { name: /restablecer contraseña/i }),
      ).not.toBeInTheDocument()
    })
  })

  describe('Submit success', () => {
    it('calls resetPassword with the token and shows success message', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.resetPassword).mockResolvedValueOnce(undefined)

      renderResetPasswordPage('/auth/reset-password?token=valid-token-123')

      await user.type(screen.getByLabelText(/nueva contraseña/i), 'NewPassword123')
      await user.type(screen.getByLabelText(/confirmar contraseña/i), 'NewPassword123')
      await user.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

      await waitFor(() => {
        expect(authService.resetPassword).toHaveBeenCalledWith(
          'valid-token-123',
          'NewPassword123',
        )
      })

      await waitFor(() => {
        expect(
          screen.getByText(/tu contraseña fue actualizada correctamente/i),
        ).toBeInTheDocument()
      })
    })

    it('redirects to /login after the success timer fires', async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true })
      const user = userEvent.setup({ advanceTimers: (ms) => vi.advanceTimersByTime(ms) })
      vi.mocked(authService.resetPassword).mockResolvedValueOnce(undefined)

      renderResetPasswordPage('/auth/reset-password?token=valid-token-123')

      await user.type(screen.getByLabelText(/nueva contraseña/i), 'NewPassword123')
      await user.type(screen.getByLabelText(/confirmar contraseña/i), 'NewPassword123')
      await user.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

      // Wait for success state
      await waitFor(() => {
        expect(
          screen.getByText(/tu contraseña fue actualizada correctamente/i),
        ).toBeInTheDocument()
      })

      // Fire the setTimeout(navigate('/login'), 2000)
      act(() => {
        vi.runAllTimers()
      })

      await waitFor(() => {
        expect(screen.getByText(/login page/i)).toBeInTheDocument()
      })

      vi.useRealTimers()
    })
  })

  describe('Backend error: invalid token', () => {
    it('shows invalid-token message when backend rejects the token', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.resetPassword).mockRejectedValueOnce(
        new Error('Token expired or already used'),
      )

      renderResetPasswordPage('/auth/reset-password?token=expired-token')

      await user.type(screen.getByLabelText(/nueva contraseña/i), 'NewPassword123')
      await user.type(screen.getByLabelText(/confirmar contraseña/i), 'NewPassword123')
      await user.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

      await waitFor(() => {
        expect(
          screen.getByText(/el enlace expiró o ya fue usado/i),
        ).toBeInTheDocument()
      })
    })
  })

  describe('TRIANGULATE: password mismatch validation', () => {
    it('shows validation error when passwords do not match (no backend call)', async () => {
      const user = userEvent.setup()

      renderResetPasswordPage('/auth/reset-password?token=valid-token-123')

      await user.type(screen.getByLabelText(/nueva contraseña/i), 'NewPassword123')
      await user.type(screen.getByLabelText(/confirmar contraseña/i), 'DifferentPassword456')
      await user.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

      await waitFor(() => {
        expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument()
      })
      expect(authService.resetPassword).not.toHaveBeenCalled()
    })
  })
})
