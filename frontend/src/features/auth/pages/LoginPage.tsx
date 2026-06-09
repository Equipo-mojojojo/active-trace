import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { LoginSchema } from '../types'
import type { LoginDTO } from '../types'
import { authService } from '../services/authService'
import { useAuth } from '@/shared/hooks/useAuth'
import { isRequiresTwoFactor } from '../types'
import { Button } from '@/shared/components/ui/Button'
import { FormField } from '@/shared/components/ui/FormField'
import { Input } from '@/shared/components/ui/Input'

export function LoginPage() {
  const navigate = useNavigate()
  const { setSession } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginDTO>({
    resolver: zodResolver(LoginSchema),
  })

  const onSubmit = async (data: LoginDTO) => {
    setServerError(null)
    try {
      const response = await authService.login(data)

      if (isRequiresTwoFactor(response)) {
        // Store session token for 2FA step — use sessionStorage (ephemeral, not localStorage)
        sessionStorage.setItem('2fa_session_token', response.session_token)
        navigate('/auth/2fa')
        return
      }

      setSession(
        response.user,
        response.roles,
        response.permissions,
        response.tenant,
        response.access_token,
      )
      navigate('/dashboard')
    } catch {
      // Generic message — do not reveal which field failed
      setServerError('Credenciales inválidas')
      // Do NOT clear the form (spec: frontend-auth §"Credenciales inválidas")
    }
  }

  return (
    <div className="relative flex min-h-screen items-center">
      {/* Full-screen background image */}
      <img
        src="/imagenlogin.png"
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
      />
      {/* Dark overlay for readability */}
      <div className="absolute inset-0 bg-slate-900/65" />

      {/* Left zone — plain dark side (~55% of image) */}
      <div className="relative z-10 flex w-full items-center justify-center px-8 lg:w-[55%]">
      <div className="w-full max-w-lg space-y-6">
        {/* Brand */}
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            active-trace
          </h1>
          <p className="mt-2 text-sm text-slate-300">
            Gestión académica y trazabilidad
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-white/10 px-10 py-12 shadow-2xl backdrop-blur-md ring-1 ring-white/20">
          <h2 className="mb-6 text-xl font-semibold text-white">
            Iniciar sesión
          </h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <FormField
              label="Email"
              htmlFor="email"
              error={errors.email?.message}
              required
              labelClassName="text-slate-200"
            >
              <Input
                id="email"
                type="email"
                autoComplete="email"
                aria-label="Email"
                className="bg-white/10 text-white placeholder:text-slate-400 ring-white/30 focus:ring-white/60"
                {...register('email')}
              />
            </FormField>

            <FormField
              label="Contraseña"
              htmlFor="password"
              error={errors.password?.message}
              required
              labelClassName="text-slate-200"
            >
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                aria-label="Contraseña"
                className="bg-white/10 text-white placeholder:text-slate-400 ring-white/30 focus:ring-white/60"
                {...register('password')}
              />
            </FormField>

            {serverError && (
              <p className="text-sm text-red-400" role="alert">
                {serverError}
              </p>
            )}

            <Button
              type="submit"
              isLoading={isSubmitting}
              className="w-full"
            >
              Ingresar
            </Button>
          </form>

          <div className="mt-4 text-center">
            <a
              href="/auth/forgot-password"
              className="text-sm text-slate-300 hover:text-white hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </a>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}
