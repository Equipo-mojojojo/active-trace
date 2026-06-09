import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'

/**
 * AuthGuard wraps protected routes.
 * - Not authenticated → redirect to /login?next=<current path>
 * - Authenticated → render the nested route via <Outlet>
 */
export function AuthGuard() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  return <Outlet />
}
