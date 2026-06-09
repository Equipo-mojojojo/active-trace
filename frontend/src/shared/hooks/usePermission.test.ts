/**
 * Tests for usePermission hook.
 * TDD: RED first.
 *
 * Scenarios:
 * - hasPermission('alumnos:ver') returns true when permission is in context
 * - hasPermission('liquidaciones:ver') returns false when NOT in context
 * - hasPermission works with multiple permissions
 */
import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'
import { usePermission } from './usePermission'
import React from 'react'

function makeAuthContext(permissions: string[]): AuthContextValue {
  return {
    user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
    roles: ['PROFESOR'],
    permissions,
    tenant: { id: 't1', nombre: 'USAL' },
    isAuthenticated: true,
    setSession: () => undefined,
    clearSession: () => undefined,
  }
}

function renderWithPermissions(permissions: string[]) {
  const ctx = makeAuthContext(permissions)
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(AuthContext.Provider, { value: ctx }, children)
  return renderHook(() => usePermission(), { wrapper })
}

describe('usePermission', () => {
  describe('hasPermission', () => {
    it('returns true when the permission is in the context', () => {
      const { result } = renderWithPermissions(['alumnos:ver', 'comisiones:ver'])
      expect(result.current.hasPermission('alumnos:ver')).toBe(true)
    })

    it('returns false when the permission is NOT in the context', () => {
      const { result } = renderWithPermissions(['alumnos:ver'])
      expect(result.current.hasPermission('liquidaciones:ver')).toBe(false)
    })

    it('returns false when the user has NO permissions', () => {
      const { result } = renderWithPermissions([])
      expect(result.current.hasPermission('alumnos:ver')).toBe(false)
    })

    it('TRIANGULATE — returns true for any permission in a multi-permission set', () => {
      const permissions = ['alumnos:ver', 'comunicacion:enviar', 'liquidaciones:ver']
      const { result } = renderWithPermissions(permissions)

      expect(result.current.hasPermission('comunicacion:enviar')).toBe(true)
      expect(result.current.hasPermission('liquidaciones:ver')).toBe(true)
      expect(result.current.hasPermission('auditoria:ver')).toBe(false)
    })
  })
})
