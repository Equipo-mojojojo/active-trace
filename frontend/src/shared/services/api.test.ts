/**
 * Tests for the Axios HTTP client with auth interceptors.
 * TDD: RED first — these tests describe the desired behavior before implementation.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import MockAdapter from 'axios-mock-adapter'

// We import the module under test after setting up mocks
let axiosMock: MockAdapter

describe('api — HTTP client with auth interceptors', () => {
  beforeEach(async () => {
    // Reset module registry to get a fresh api instance
    vi.resetModules()
  })

  afterEach(() => {
    if (axiosMock) axiosMock.restore()
  })

  it('injects Authorization header when access token is set', async () => {
    const { api, setAccessToken } = await import('./api')
    axiosMock = new MockAdapter(api)
    axiosMock.onGet('/api/test').reply((config) => {
      const auth = config.headers?.['Authorization']
      return [200, { auth }]
    })

    setAccessToken('my-token-123')
    const response = await api.get('/api/test')

    expect(response.data.auth).toBe('Bearer my-token-123')
  })

  it('does NOT inject Authorization header when no token is set', async () => {
    vi.resetModules()
    const { api, setAccessToken } = await import('./api')
    axiosMock = new MockAdapter(api)
    axiosMock.onGet('/api/test').reply((config) => {
      return [200, { auth: config.headers?.['Authorization'] ?? null }]
    })

    setAccessToken(null)
    const response = await api.get('/api/test')

    expect(response.data.auth).toBeNull()
  })

  it('retries original request transparently after 401 + successful refresh', async () => {
    vi.resetModules()
    const { api, setAccessToken } = await import('./api')
    axiosMock = new MockAdapter(api)

    setAccessToken('expired-token')

    let requestCount = 0
    axiosMock.onGet('/api/protected').reply(() => {
      requestCount++
      if (requestCount === 1) {
        // First call: token expired
        return [401, { detail: 'Token expired' }]
      }
      // Retry: new token injected
      return [200, { data: 'success' }]
    })

    axiosMock.onPost('/auth/refresh').reply(() => {
      return [200, { access_token: 'new-token-456' }]
    })

    const response = await api.get('/api/protected')

    expect(response.data.data).toBe('success')
    expect(requestCount).toBe(2)
  })

  it('only executes ONE refresh when multiple 401s arrive simultaneously', async () => {
    vi.resetModules()
    const { api, setAccessToken } = await import('./api')
    axiosMock = new MockAdapter(api)

    setAccessToken('expired-token')

    let refreshCount = 0
    axiosMock.onPost('/auth/refresh').reply(async () => {
      refreshCount++
      // Simulate async refresh
      await new Promise((r) => setTimeout(r, 10))
      return [200, { access_token: 'new-token-999' }]
    })

    let getCount = 0
    axiosMock.onGet('/api/endpoint').reply(() => {
      getCount++
      if (getCount <= 3) return [401, {}]
      return [200, { ok: true }]
    })

    // Fire 3 simultaneous requests
    const results = await Promise.all([
      api.get('/api/endpoint'),
      api.get('/api/endpoint'),
      api.get('/api/endpoint'),
    ])

    expect(refreshCount).toBe(1)
    results.forEach((r) => expect(r.data.ok).toBe(true))
  })
})
