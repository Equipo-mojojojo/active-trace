import { Link } from 'react-router-dom'
import { useAuth } from '@/shared/hooks/useAuth'

export function NotFoundPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-slate-300">404</h1>
        <h2 className="text-2xl font-semibold text-slate-900">
          Página no encontrada
        </h2>
        <p className="text-sm text-slate-500">
          La página que buscás no existe o fue movida.
        </p>
        <Link
          to={isAuthenticated ? '/dashboard' : '/login'}
          className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          {isAuthenticated ? 'Volver al dashboard' : 'Ir al login'}
        </Link>
      </div>
    </div>
  )
}
