import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { TwoFactorSchema } from '../types'
import type { TwoFactorDTO } from '../types'
import { authService } from '../services/authService'
import { useAuth } from '@/shared/hooks/useAuth'
import { Button } from '@/shared/components/ui/Button'
import { FormField } from '@/shared/components/ui/FormField'
import { Input } from '@/shared/components/ui/Input'

export function TwoFactorPage() {
  const navigate = useNavigate()
  const { setSession } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)

  // If there is no session token, redirect to /login
  // (spec: frontend-auth §"Acceso directo a /auth/2fa sin sesión parcial")
  const sessionToken = sessionStorage.getItem('2fa_session_token')
  useEffect(() => {
    if (!sessionToken) {
      navigate('/login', { replace: true })
    }
  }, [sessionToken, navigate])

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TwoFactorDTO>({
    resolver: zodResolver(TwoFactorSchema),
  })

  const onSubmit = async (data: TwoFactorDTO) => {
    if (!sessionToken) return
    setServerError(null)
    try {
      const response = await authService.verifyTwoFactor(data, sessionToken)
      sessionStorage.removeItem('2fa_session_token')
      setSession(
        response.user,
        response.roles,
        response.permissions,
        response.tenant,
        response.access_token,
      )
      navigate('/dashboard')
    } catch {
      setServerError('Código inválido o expirado')
      reset() // Clear code field for retry (spec: frontend-auth §"Código TOTP incorrecto")
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            active-trace
          </h1>
          <p className="mt-2 text-sm text-slate-600">Verificación en dos pasos</p>
        </div>

        <div className="rounded-xl bg-white px-8 py-10 shadow-sm ring-1 ring-slate-200">
          <h2 className="mb-2 text-xl font-semibold text-slate-900">
            Código de verificación
          </h2>
          <p className="mb-6 text-sm text-slate-500">
            Ingresá el código de 6 dígitos de tu aplicación autenticadora.
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <FormField
              label="Código TOTP"
              htmlFor="code"
              error={errors.code?.message}
              required
            >
              <Input
                id="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                placeholder="000000"
                aria-label="Código TOTP"
                {...register('code')}
              />
            </FormField>

            {serverError && (
              <p className="text-sm text-red-600" role="alert">
                {serverError}
              </p>
            )}

            <Button
              type="submit"
              isLoading={isSubmitting}
              className="w-full"
            >
              Verificar
            </Button>
          </form>

          <div className="mt-4 text-center">
            <a
              href="/login"
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
            >
              Volver al inicio de sesión
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
