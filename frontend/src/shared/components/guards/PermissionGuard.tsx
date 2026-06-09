import { Navigate, Outlet } from 'react-router-dom'
import { usePermission } from '@/shared/hooks/usePermission'

interface PermissionGuardProps {
  /** Required permission(s). Array = OR logic (access if user has ANY). */
  permission: string | string[]
}

/**
 * PermissionGuard wraps routes that require a specific permission.
 * Assumes AuthGuard has already run (user is authenticated).
 * - User lacks permission → redirect to /403
 * - User has permission → render the nested route via <Outlet>
 */
export function PermissionGuard({ permission }: PermissionGuardProps) {
  const { hasPermission } = usePermission()

  const allowed = Array.isArray(permission)
    ? permission.some((p) => hasPermission(p))
    : hasPermission(permission)

  if (!allowed) {
    return <Navigate to="/403" replace />
  }

  return <Outlet />
}
