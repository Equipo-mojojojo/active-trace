import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'
import { authService } from '@/features/auth/services/authService'
import { Sidebar } from './Sidebar'
import { Button } from '@/shared/components/ui/Button'
import { useState } from 'react'

export function AppLayout() {
  const { user, tenant, clearSession } = useAuth()
  const navigate = useNavigate()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  /**
   * Logout handler.
   * Spec: frontend-auth §"Logout ante fallo del backend"
   * Even if the backend fails, we clear the session locally and redirect (fail-safe).
   */
  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await authService.logout()
    } catch {
      // Fail-safe: ignore backend errors on logout
    } finally {
      clearSession()
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
          <div className="flex items-center gap-2">
            {tenant && (
              <span className="text-sm font-medium text-slate-600">
                {tenant.nombre}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-slate-700" aria-label="Nombre del usuario">
                {user.nombre}
              </span>
            )}
            <Button
              variant="ghost"
              onClick={handleLogout}
              isLoading={isLoggingOut}
              aria-label="Cerrar sesión"
            >
              Cerrar sesión
            </Button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
