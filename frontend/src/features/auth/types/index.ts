import { z } from 'zod'

// ─── Request DTOs ─────────────────────────────────────────────────────────────

export const LoginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

export type LoginDTO = z.infer<typeof LoginSchema>

export const TwoFactorSchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d{6}$/, 'El código debe contener solo números'),
})

export type TwoFactorDTO = z.infer<typeof TwoFactorSchema>

export const ForgotPasswordSchema = z.object({
  email: z.string().email('Email inválido'),
})

export type ForgotPasswordDTO = z.infer<typeof ForgotPasswordSchema>

export const ResetPasswordSchema = z
  .object({
    password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
    confirmPassword: z.string().min(1, 'Confirmá la contraseña'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })

export type ResetPasswordDTO = z.infer<typeof ResetPasswordSchema>

// ─── Response types ───────────────────────────────────────────────────────────

export interface AuthUser {
  id: string
  nombre: string
  email: string
}

export interface AuthTenant {
  id: string
  nombre: string
}

/** Response when login requires 2FA */
export interface RequiresTwoFactorResponse {
  requires_2fa: true
  session_token: string
}

/** Full auth response after successful login or 2FA verification */
export interface AuthResponse {
  user: AuthUser
  access_token: string
  permissions: string[]
  roles: string[]
  tenant: AuthTenant
  requires_2fa?: false
}

/** Union type for login response */
export type LoginResponse = AuthResponse | RequiresTwoFactorResponse

export function isRequiresTwoFactor(
  response: LoginResponse,
): response is RequiresTwoFactorResponse {
  return (response as RequiresTwoFactorResponse).requires_2fa === true
}
