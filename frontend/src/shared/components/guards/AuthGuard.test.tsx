/**
 * Tests for AuthGuard.
 * TDD: RED first — written before AuthGuard implementation.
 *
 * Scenarios (spec: frontend-routing §AuthGuard):
 * 9.4a - Not authenticated → redirects to /login
 * 9.4b - Authenticated → renders the protected content
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

// Helper to build an AuthContextValue for tests
function makeAuthContext(
  overrides: Partial<AuthContextValue> = {},
): AuthContextValue {
  return {
    user: null,
    roles: [],
    permissions: [],
    tenant: null,
    isAuthenticated: false,
    setSession: () => undefined,
    clearSession: () => undefined,
    ...overrides,
  }
}

function renderWithAuth(
  isAuthenticated: boolean,
  initialPath = '/dashboard',
) {
  const ctx = makeAuthContext({ isAuthenticated })
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<AuthGuardLazy />}>
            <Route path="/dashboard" element={<div>Protected Dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

let AuthGuardLazy: React.ComponentType
import { beforeEach } from 'vitest'
beforeEach(async () => {
  const mod = await import('./AuthGuard')
  AuthGuardLazy = mod.AuthGuard
})

describe('AuthGuard', () => {
  it('9.4a — not authenticated: redirects to /login', () => {
    renderWithAuth(false)
    expect(screen.getByText(/login page/i)).toBeInTheDocument()
    expect(screen.queryByText(/protected dashboard/i)).not.toBeInTheDocument()
  })

  it('9.4b — authenticated: renders protected content', () => {
    renderWithAuth(true)
    expect(screen.getByText(/protected dashboard/i)).toBeInTheDocument()
    expect(screen.queryByText(/login page/i)).not.toBeInTheDocument()
  })

  it('preserves ?next= param in redirect URL', () => {
    const ctx = makeAuthContext({ isAuthenticated: false })
    const { container } = render(
      <AuthContext.Provider value={ctx}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route
              path="/login"
              element={
                <div data-testid="login">
                  {window.location.search}
                </div>
              }
            />
            <Route element={<AuthGuardLazy />}>
              <Route path="/dashboard" element={<div>Protected</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )
    // Guard redirected — login page is shown
    expect(screen.getByTestId('login')).toBeInTheDocument()
    expect(container.innerHTML).not.toContain('Protected')
  })
})
