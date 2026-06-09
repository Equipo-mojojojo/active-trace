import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ResetPasswordSchema } from '../types'
import type { ResetPasswordDTO } from '../types'
import { authService } from '../services/authService'
import { Button } from '@/shared/components/ui/Button'
import { FormField } from '@/shared/components/ui/FormField'
import { Input } from '@/shared/components/ui/Input'

type PageState = 'form' | 'success' | 'invalid-token'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')
  const [pageState, setPageState] = useState<PageState>(
    token ? 'form' : 'invalid-token',
  )

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordDTO>({
    resolver: zodResolver(ResetPasswordSchema),
  })

  const onSubmit = async (data: ResetPasswordDTO) => {
    if (!token) return
    try {
      await authService.resetPassword(token, data.password)
      setPageState('success')
      setTimeout(() => navigate('/login'), 2000)
    } catch {
      // Token inválido o expirado (spec: frontend-auth §"Token inválido o expirado")
      setPageState('invalid-token')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            active-trace
          </h1>
          <p className="mt-2 text-sm text-slate-600">Restablecer contraseña</p>
        </div>

        <div className="rounded-xl bg-white px-8 py-10 shadow-sm ring-1 ring-slate-200">
          {pageState === 'success' && (
            <div className="text-center">
              <p className="text-sm text-green-700">
                Tu contraseña fue actualizada correctamente. Redirigiendo al login...
              </p>
            </div>
          )}

          {pageState === 'invalid-token' && (
            <div className="text-center space-y-3">
              <p className="text-sm text-red-700">
                El enlace expiró o ya fue usado. Solicitá uno nuevo.
              </p>
              <a
                href="/auth/forgot-password"
                className="text-sm text-primary-600 hover:underline"
              >
                Solicitar nuevo enlace
              </a>
            </div>
          )}

          {pageState === 'form' && (
            <>
              <h2 className="mb-6 text-xl font-semibold text-slate-900">
                Nueva contraseña
              </h2>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
                <FormField
                  label="Nueva contraseña"
                  htmlFor="password"
                  error={errors.password?.message}
                  required
                >
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    aria-label="Nueva contraseña"
                    {...register('password')}
                  />
                </FormField>

                <FormField
                  label="Confirmar contraseña"
                  htmlFor="confirmPassword"
                  error={errors.confirmPassword?.message}
                  required
                >
                  <Input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    aria-label="Confirmar contraseña"
                    {...register('confirmPassword')}
                  />
                </FormField>

                <Button
                  type="submit"
                  isLoading={isSubmitting}
                  className="w-full"
                >
                  Restablecer contraseña
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
