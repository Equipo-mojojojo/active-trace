/**
 * Tests for ForgotPasswordPage.
 * TDD: RED first.
 *
 * Scenarios:
 * - Render: shows email field and send button
 * - Submit success: calls authService.requestPasswordReset and shows generic confirmation
 * - Validation: empty email → shows error without calling backend
 * - TRIANGULATE: even if backend errors, shows generic confirmation message
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    requestPasswordReset: vi.fn(),
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

function renderForgotPasswordPage() {
  const ctx = makeAuthContext()
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={['/auth/forgot-password']}>
        <ForgotPasswordPageLazy />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

let ForgotPasswordPageLazy: React.ComponentType
beforeEach(async () => {
  const mod = await import('./ForgotPasswordPage')
  ForgotPasswordPageLazy = mod.ForgotPasswordPage
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('ForgotPasswordPage', () => {
  describe('Render', () => {
    it('shows an email field and a send button', () => {
      renderForgotPasswordPage()

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /enviar instrucciones/i }),
      ).toBeInTheDocument()
    })
  })

  describe('Validation: empty email', () => {
    it('shows validation error and does NOT call the backend when email is empty', async () => {
      const user = userEvent.setup()
      renderForgotPasswordPage()

      await user.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

      await waitFor(() => {
        expect(screen.getByText(/email inválido/i)).toBeInTheDocument()
      })
      expect(authService.requestPasswordReset).not.toHaveBeenCalled()
    })
  })

  describe('Submit success', () => {
    it('calls requestPasswordReset and shows generic confirmation message', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.requestPasswordReset).mockResolvedValueOnce(undefined)

      renderForgotPasswordPage()

      await user.type(screen.getByLabelText(/email/i), 'user@example.com')
      await user.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

      await waitFor(() => {
        expect(
          screen.getByText(/si tu email está registrado/i),
        ).toBeInTheDocument()
      })

      expect(authService.requestPasswordReset).toHaveBeenCalledWith({
        email: 'user@example.com',
      })
    })
  })

  describe('TRIANGULATE: backend error still shows confirmation', () => {
    it('shows the generic confirmation even when backend throws an error', async () => {
      const user = userEvent.setup()
      vi.mocked(authService.requestPasswordReset).mockRejectedValueOnce(
        new Error('Server error'),
      )

      renderForgotPasswordPage()

      await user.type(screen.getByLabelText(/email/i), 'user@example.com')
      await user.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

      // Spec: always show generic message regardless of errors (security by design)
      await waitFor(() => {
        expect(
          screen.getByText(/si tu email está registrado/i),
        ).toBeInTheDocument()
      })
    })
  })
})
