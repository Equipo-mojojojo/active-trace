import { createContext, useState, useCallback, useEffect } from 'react'
import type { ReactNode } from 'react'
import { setAccessToken } from '@/shared/services/api'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string
  nombre: string
  email: string
}

export interface AuthTenant {
  id: string
  nombre: string
}

export interface AuthState {
  user: AuthUser | null
  roles: string[]
  permissions: string[]
  tenant: AuthTenant | null
  isAuthenticated: boolean
}

export interface AuthContextValue extends AuthState {
  /** Populate session after a successful login or refresh. */
  setSession: (
    user: AuthUser,
    roles: string[],
    permissions: string[],
    tenant: AuthTenant,
    accessToken: string,
  ) => void
  /** Clear session (logout). */
  clearSession: () => void
}

// ─── Context ─────────────────────────────────────────────────────────────────

const initialState: AuthState = {
  user: null,
  roles: [],
  permissions: [],
  tenant: null,
  isAuthenticated: false,
}

export const AuthContext = createContext<AuthContextValue | null>(null)

// ─── Provider ────────────────────────────────────────────────────────────────

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>(initialState)

  const setSession = useCallback(
    (
      user: AuthUser,
      roles: string[],
      permissions: string[],
      tenant: AuthTenant,
      accessToken: string,
    ) => {
      setAccessToken(accessToken)
      setState({
        user,
        roles,
        permissions,
        tenant,
        isAuthenticated: true,
      })
    },
    [],
  )

  const clearSession = useCallback(() => {
    setAccessToken(null)
    setState(initialState)
  }, [])

  /**
   * Session restoration on mount.
   * Spec: frontend-auth §"Restauración de sesión al iniciar la app"
   * Attempt to refresh the access token. If the httpOnly cookie is valid,
   * the backend returns a new access token and the session is restored.
   * If the refresh fails, isAuthenticated stays false → user sees /login.
   */
  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      try {
        // Import lazily to avoid circular dependency at module load time
        const { authService } = await import('@/features/auth/services/authService')
        const response = await authService.refresh()
        if (!cancelled) {
          setSession(
            response.user,
            response.roles,
            response.permissions,
            response.tenant,
            response.access_token,
          )
        }
      } catch {
        // No active session — stay unauthenticated
        if (!cancelled) {
          setState(initialState)
        }
      }
    }

    restoreSession()

    return () => {
      cancelled = true
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, setSession, clearSession }}>
      {children}
    </AuthContext.Provider>
  )
}
