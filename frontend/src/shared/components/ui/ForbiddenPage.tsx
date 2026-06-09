import { Link } from 'react-router-dom'

export function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-slate-300">403</h1>
        <h2 className="text-2xl font-semibold text-slate-900">Acceso denegado</h2>
        <p className="text-sm text-slate-500">
          No tenés permiso para ver esta página.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          Volver al dashboard
        </Link>
      </div>
    </div>
  )
}
