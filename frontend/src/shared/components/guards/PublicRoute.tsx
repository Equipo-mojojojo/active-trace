import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'

/**
 * PublicRoute: wraps routes that should NOT be accessible when authenticated.
 * If user is authenticated → redirect to /dashboard.
 * If not authenticated → render the route normally.
 *
 * Spec: frontend-routing §"Usuario autenticado visita /login"
 */
export function PublicRoute() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
