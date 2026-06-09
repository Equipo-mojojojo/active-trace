import { useContext } from 'react'
import { AuthContext } from '@/shared/context/AuthContext'
import type { AuthContextValue } from '@/shared/context/AuthContext'

/**
 * Hook to consume the AuthContext.
 * Throws if used outside of AuthProvider.
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error('useAuth must be used within an <AuthProvider>')
  }
  return ctx
}
