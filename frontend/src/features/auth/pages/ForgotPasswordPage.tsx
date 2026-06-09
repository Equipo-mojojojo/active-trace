import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ForgotPasswordSchema } from '../types'
import type { ForgotPasswordDTO } from '../types'
import { authService } from '../services/authService'
import { Button } from '@/shared/components/ui/Button'
import { FormField } from '@/shared/components/ui/FormField'
import { Input } from '@/shared/components/ui/Input'

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordDTO>({
    resolver: zodResolver(ForgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordDTO) => {
    try {
      await authService.requestPasswordReset(data)
    } catch {
      // Swallow errors — always show generic confirmation (spec: frontend-auth §Recuperación)
    } finally {
      setSubmitted(true)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            active-trace
          </h1>
          <p className="mt-2 text-sm text-slate-600">Recuperar contraseña</p>
        </div>

        <div className="rounded-xl bg-white px-8 py-10 shadow-sm ring-1 ring-slate-200">
          {submitted ? (
            <div className="text-center">
              <p className="text-sm text-slate-700">
                Si tu email está registrado, recibirás las instrucciones en breve.
              </p>
              <div className="mt-4">
                <a
                  href="/login"
                  className="text-sm text-primary-600 hover:underline"
                >
                  Volver al inicio de sesión
                </a>
              </div>
            </div>
          ) : (
            <>
              <h2 className="mb-2 text-xl font-semibold text-slate-900">
                Recuperar contraseña
              </h2>
              <p className="mb-6 text-sm text-slate-500">
                Ingresá tu email y te enviaremos un enlace para restablecer tu contraseña.
              </p>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
                <FormField
                  label="Email"
                  htmlFor="email"
                  error={errors.email?.message}
                  required
                >
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    aria-label="Email"
                    {...register('email')}
                  />
                </FormField>

                <Button
                  type="submit"
                  isLoading={isSubmitting}
                  className="w-full"
                >
                  Enviar instrucciones
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
            </>
          )}
        </div>
      </div>
    </div>
  )
}
