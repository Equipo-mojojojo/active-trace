import { api } from '@/shared/services/api'
import type {
  LoginDTO,
  TwoFactorDTO,
  ForgotPasswordDTO,
  LoginResponse,
  AuthResponse,
} from '../types'

export const authService = {
  /**
   * Attempt login with email + password.
   * Returns either a full AuthResponse or a RequiresTwoFactorResponse.
   */
  login: (data: LoginDTO): Promise<LoginResponse> =>
    api.post<LoginResponse>('/auth/login', data).then((r) => r.data),

  /**
   * Verify a TOTP code during the 2FA step.
   * `sessionToken` is the ephemeral token returned by the server when requires_2fa is true.
   */
  verifyTwoFactor: (
    data: TwoFactorDTO,
    sessionToken: string,
  ): Promise<AuthResponse> =>
    api
      .post<AuthResponse>('/auth/2fa/verify', {
        code: data.code,
        session_token: sessionToken,
      })
      .then((r) => r.data),

  /**
   * Request a password reset email.
   * The server always returns 200 regardless of whether the email exists.
   */
  requestPasswordReset: (data: ForgotPasswordDTO): Promise<void> =>
    api
      .post('/auth/password/reset-request', { email: data.email })
      .then(() => undefined),

  /**
   * Complete a password reset with the token from the email link.
   */
  resetPassword: (token: string, newPassword: string): Promise<void> =>
    api
      .post('/auth/password/reset', { token, new_password: newPassword })
      .then(() => undefined),

  /**
   * Use the refresh token (httpOnly cookie) to get a new access token.
   * Called on app mount to restore session.
   */
  refresh: (): Promise<AuthResponse> =>
    api.post<AuthResponse>('/auth/refresh').then((r) => r.data),

  /**
   * Logout: invalidates the refresh token on the server.
   * The interceptor clears the access token automatically on failure/success.
   */
  logout: (): Promise<void> =>
    api.post('/auth/logout').then(() => undefined),
}
