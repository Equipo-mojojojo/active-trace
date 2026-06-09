import { useAuth } from './useAuth'

/**
 * Returns a function that checks if the current user has a specific permission.
 * Permission format: "modulo:accion" (e.g. "alumnos:ver", "liquidaciones:ver")
 */
export function usePermission() {
  const { permissions } = useAuth()

  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission)
  }

  return { hasPermission }
}
