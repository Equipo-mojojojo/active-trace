/**
 * Tests for authService.
 * TDD: RED first — tests written before implementation.
 *
 * Scenarios covered:
 * - login: calls api.post('/auth/login', data) and returns result
 * - verifyTwoFactor: calls api.post('/auth/2fa/verify', ...) and returns result
 * - requestPasswordReset: calls api.post('/auth/password/reset-request', ...)
 * - resetPassword: calls api.post('/auth/password/reset', ...)
 * - refresh: calls api.post('/auth/refresh') and returns result
 * - logout: calls api.post('/auth/logout')
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the api module before importing authService
vi.mock('@/shared/services/api', () => ({
  api: {
    post: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { authService } from './authService'
import type { LoginDTO, TwoFactorDTO, ForgotPasswordDTO, AuthResponse } from '../types'

const mockAuthResponse: AuthResponse = {
  user: { id: 'u1', nombre: 'Test User', email: 'test@example.com' },
  access_token: 'token-abc',
  permissions: ['alumnos:ver'],
  roles: ['PROFESOR'],
  tenant: { id: 't1', nombre: 'USAL' },
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authService', () => {
  describe('login', () => {
    it('calls api.post with /auth/login and the login data', async () => {
      const loginData: LoginDTO = { email: 'test@example.com', password: 'password123' }
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockAuthResponse })

      const result = await authService.login(loginData)

      expect(api.post).toHaveBeenCalledWith('/auth/login', loginData)
      expect(result).toEqual(mockAuthResponse)
    })

    it('propagates errors from the API', async () => {
      const loginData: LoginDTO = { email: 'test@example.com', password: 'wrong' }
      const error = new Error('401 Unauthorized')
      vi.mocked(api.post).mockRejectedValueOnce(error)

      await expect(authService.login(loginData)).rejects.toThrow('401 Unauthorized')
    })
  })

  describe('verifyTwoFactor', () => {
    it('calls api.post with /auth/2fa/verify and the correct payload', async () => {
      const twoFactorData: TwoFactorDTO = { code: '123456' }
      const sessionToken = 'partial-session-xyz'
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockAuthResponse })

      const result = await authService.verifyTwoFactor(twoFactorData, sessionToken)

      expect(api.post).toHaveBeenCalledWith('/auth/2fa/verify', {
        code: '123456',
        session_token: 'partial-session-xyz',
      })
      expect(result).toEqual(mockAuthResponse)
    })
  })

  describe('requestPasswordReset', () => {
    it('calls api.post with /auth/password/reset-request and the email', async () => {
      const forgotData: ForgotPasswordDTO = { email: 'user@example.com' }
      vi.mocked(api.post).mockResolvedValueOnce({ data: undefined })

      await authService.requestPasswordReset(forgotData)

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset-request', {
        email: 'user@example.com',
      })
    })

    it('returns void (undefined) on success', async () => {
      const forgotData: ForgotPasswordDTO = { email: 'user@example.com' }
      vi.mocked(api.post).mockResolvedValueOnce({ data: {} })

      const result = await authService.requestPasswordReset(forgotData)

      expect(result).toBeUndefined()
    })
  })

  describe('resetPassword', () => {
    it('calls api.post with /auth/password/reset and the token + new password', async () => {
      const token = 'reset-token-123'
      const newPassword = 'newPassword123'
      vi.mocked(api.post).mockResolvedValueOnce({ data: undefined })

      await authService.resetPassword(token, newPassword)

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset', {
        token,
        new_password: newPassword,
      })
    })

    it('returns void (undefined) on success', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: {} })

      const result = await authService.resetPassword('token', 'newPass123')

      expect(result).toBeUndefined()
    })
  })

  describe('refresh', () => {
    it('calls api.post with /auth/refresh and returns auth response', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: mockAuthResponse })

      const result = await authService.refresh()

      expect(api.post).toHaveBeenCalledWith('/auth/refresh')
      expect(result).toEqual(mockAuthResponse)
    })

    it('propagates errors when refresh fails', async () => {
      const error = new Error('Refresh failed')
      vi.mocked(api.post).mockRejectedValueOnce(error)

      await expect(authService.refresh()).rejects.toThrow('Refresh failed')
    })
  })

  describe('logout', () => {
    it('calls api.post with /auth/logout', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: undefined })

      await authService.logout()

      expect(api.post).toHaveBeenCalledWith('/auth/logout')
    })

    it('returns void (undefined) on success', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ data: {} })

      const result = await authService.logout()

      expect(result).toBeUndefined()
    })
  })
})
