/**
 * Centralized Axios HTTP client for active-trace.
 *
 * Strategy:
 * - Access token: stored in module-level variable (memory, NOT localStorage).
 *   This prevents XSS from stealing tokens.
 * - Refresh token: managed by the backend as an httpOnly cookie.
 * - Queue: when multiple requests get 401 simultaneously, only ONE refresh
 *   is executed. Others wait in pendingRequests and are retried with the new token.
 */
import axios from 'axios'
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'

// ─── Token store (memory only) ───────────────────────────────────────────────

let _accessToken: string | null = null

/** Set the access token in memory. Pass null to clear. */
export function setAccessToken(token: string | null): void {
  _accessToken = token
}

/** Get the current access token. */
export function getAccessToken(): string | null {
  return _accessToken
}

// ─── Axios instance ──────────────────────────────────────────────────────────

export const api = axios.create({
  baseURL: import.meta.env['VITE_API_URL'] ?? '/api/v1',
  withCredentials: true, // send httpOnly refresh-token cookie automatically
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request interceptor — inject Authorization header ───────────────────────

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (_accessToken) {
    config.headers['Authorization'] = `Bearer ${_accessToken}`
  }
  return config
})

// ─── Response interceptor — refresh token on 401 ────────────────────────────

/** Flag: a refresh is already in flight. */
let isRefreshing = false

/** Queue of callbacks waiting for the new token. */
type PendingCallback = (token: string) => void
let pendingRequests: PendingCallback[] = []

/** Notify all queued requests with the new token. */
function resolvePending(token: string): void {
  pendingRequests.forEach((cb) => cb(token))
  pendingRequests = []
}

/** Reject all queued requests (refresh failed). */
function rejectPending(): void {
  pendingRequests = []
}

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error)

    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    const is401 = error.response?.status === 401
    const isAuthEndpoint = originalRequest.url?.includes('/auth/')

    // 401 from any auth endpoint (login, refresh, 2fa) → don't attempt refresh,
    // just let the caller handle it (wrong credentials, expired session, etc.)
    if (is401 && isAuthEndpoint) {
      setAccessToken(null)
      rejectPending()
      isRefreshing = false
      if (originalRequest.url?.includes('/auth/refresh') &&
          !window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/auth')) {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // 401 on a regular endpoint: attempt refresh
    if (is401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        // Another refresh is already in flight → join the queue
        return new Promise<AxiosResponse>((resolve) => {
          pendingRequests.push((token: string) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const { data } = await api.post<{ access_token: string }>('/auth/refresh')
        const newToken = data.access_token
        setAccessToken(newToken)
        resolvePending(newToken)
        isRefreshing = false
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        setAccessToken(null)
        rejectPending()
        isRefreshing = false
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)
