/**
 * Tests for PermissionGuard.
 * TDD: RED first.
 *
 * Scenarios (spec: frontend-routing §PermissionGuard):
 * 9.5a - User without required permission → redirects to /403
 * 9.5b - User with required permission → renders content
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

function makeAuthContext(permissions: string[]): AuthContextValue {
  return {
    user: { id: 'u1', nombre: 'Test', email: 'test@test.com' },
    roles: ['PROFESOR'],
    permissions,
    tenant: { id: 't1', nombre: 'USAL' },
    isAuthenticated: true,
    setSession: () => undefined,
    clearSession: () => undefined,
  }
}

let PermissionGuardLazy: React.ComponentType<{ permission: string }>

beforeEach(async () => {
  const mod = await import('./PermissionGuard')
  PermissionGuardLazy = mod.PermissionGuard
})

function renderWithPermissions(userPermissions: string[], requiredPermission: string) {
  const ctx = makeAuthContext(userPermissions)
  return render(
    <AuthContext.Provider value={ctx}>
      <MemoryRouter initialEntries={['/liquidaciones']}>
        <Routes>
          <Route path="/403" element={<div>Forbidden Page</div>} />
          <Route element={<PermissionGuardLazy permission={requiredPermission} />}>
            <Route path="/liquidaciones" element={<div>Liquidaciones Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('PermissionGuard', () => {
  it('9.5a — user without permission: redirects to /403', () => {
    renderWithPermissions(['alumnos:ver'], 'liquidaciones:ver')
    expect(screen.getByText(/forbidden page/i)).toBeInTheDocument()
    expect(screen.queryByText(/liquidaciones content/i)).not.toBeInTheDocument()
  })

  it('9.5b — user with required permission: renders content', () => {
    renderWithPermissions(['alumnos:ver', 'liquidaciones:ver'], 'liquidaciones:ver')
    expect(screen.getByText(/liquidaciones content/i)).toBeInTheDocument()
    expect(screen.queryByText(/forbidden page/i)).not.toBeInTheDocument()
  })

  it('TRIANGULATE — user with multiple permissions still works', () => {
    renderWithPermissions(
      ['alumnos:ver', 'comunicacion:enviar', 'liquidaciones:ver'],
      'comunicacion:enviar',
    )
    expect(screen.getByText(/liquidaciones content/i)).toBeInTheDocument()
  })
})
