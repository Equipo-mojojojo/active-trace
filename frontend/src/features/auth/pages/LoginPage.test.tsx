/**
 * Tests for LoginPage.
 * TDD: these tests are written BEFORE the LoginPage implementation.
 *
 * Scenarios covered (from spec: frontend-auth):
 * 9.1 - Render initial: shows email and password fields
 * 9.1 - Submit with empty fields: shows validation errors (no backend call)
 * 9.2 - Successful login without 2FA: context becomes authenticated, redirect to /dashboard
 * 9.3 - Invalid credentials (401): shows "Credenciales inválidas", form NOT cleared
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/shared/context/AuthContext'

// Mock the authService module
vi.mock('@/features/auth/services/authService', () => ({
  authService: {
    login: vi.fn(),
    refresh: vi.fn().mockRejectedValue(new Error('no session')),
  },
}))

import { authService } from '@/features/auth/services/authService'
import type { AuthResponse, RequiresTwoFactorResponse } from '../types'

// Helper to create a fresh QueryClient for each test
function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderLoginPage() {
  const qc = makeQueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPageLazy />} />
            <Route path="/dashboard" element={<div>Dashboard Page</div>} />
            <Route path="/auth/2fa" element={<div>2FA Page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

// Lazy import to allow vi.mock to be hoisted
let LoginPageLazy: React.ComponentType
beforeEach(async () => {
  const mod = await import('./LoginPage')
  LoginPageLazy = mod.LoginPage
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('LoginPage', () => {
  describe('9.1 — Render and validation', () => {
    it('shows email and password fields on initial render', async () => {
      renderLoginPage()

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /ingresar/i }),
      ).toBeInTheDocument()
    })

    it('shows validation errors when submitting empty form (no backend call)', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await user.click(screen.getByRole('button', { name: /ingresar/i }))

      await waitFor(() => {
        expect(screen.getByText(/email inválido/i)).toBeInTheDocument()
      })
      await waitFor(() => {
        expect(
          screen.getByText(/la contraseña es requerida/i),
        ).toBeInTheDocument()
      })

      expect(authService.login).not.toHaveBeenCalled()
    })
  })

  describe('9.2 — Successful login without 2FA', () => {
    it('sets session and redirects to /dashboard', async () => {
      const user = userEvent.setup()
      const mockResponse: AuthResponse = {
        user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
        access_token: 'token-abc',
        permissions: ['alumnos:ver'],
        roles: ['PROFESOR'],
        tenant: { id: 't1', nombre: 'USAL' },
      }
      vi.mocked(authService.login).mockResolvedValueOnce(mockResponse)

      renderLoginPage()

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/contraseña/i), 'password123')
      await user.click(screen.getByRole('button', { name: /ingresar/i }))

      await waitFor(() => {
        expect(screen.getByText(/dashboard page/i)).toBeInTheDocument()
      })
    })
  })

  describe('9.3 — Invalid credentials (401)', () => {
    it('shows "Credenciales inválidas" and does NOT clear the form', async () => {
      const user = userEvent.setup()
      const axiosError = {
        isAxiosError: true,
        response: { status: 401, data: { detail: 'Invalid credentials' } },
      }
      vi.mocked(authService.login).mockRejectedValueOnce(axiosError)

      renderLoginPage()

      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com')
      await user.type(screen.getByLabelText(/contraseña/i), 'wrongpassword')
      await user.click(screen.getByRole('button', { name: /ingresar/i }))

      await waitFor(() => {
        expect(screen.getByText(/credenciales inválidas/i)).toBeInTheDocument()
      })

      // Form fields are NOT cleared
      expect(screen.getByLabelText<HTMLInputElement>(/email/i).value).toBe(
        'wrong@example.com',
      )
      expect(
        screen.getByLabelText<HTMLInputElement>(/contraseña/i).value,
      ).toBe('wrongpassword')
    })
  })

  describe('2FA redirect scenario', () => {
    it('redirects to /auth/2fa when backend responds with requires_2fa: true', async () => {
      const user = userEvent.setup()
      const mockResponse: RequiresTwoFactorResponse = {
        requires_2fa: true,
        session_token: 'partial-session-xyz',
      }
      vi.mocked(authService.login).mockResolvedValueOnce(mockResponse)

      renderLoginPage()

      await user.type(screen.getByLabelText(/email/i), 'admin@example.com')
      await user.type(screen.getByLabelText(/contraseña/i), 'password123')
      await user.click(screen.getByRole('button', { name: /ingresar/i }))

      await waitFor(() => {
        expect(screen.getByText(/2fa page/i)).toBeInTheDocument()
      })
    })
  })
})
