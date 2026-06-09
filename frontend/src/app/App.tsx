import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/shared/context/AuthContext'
import { router } from './router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
})

/**
 * Root component.
 * Provider order matters:
 * 1. AuthProvider — provides session state consumed by guards
 * 2. QueryClientProvider — provides server state (TanStack Query)
 * 3. RouterProvider — provides routing (reads auth state via context)
 */
export function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors />
      </QueryClientProvider>
    </AuthProvider>
  )
}
