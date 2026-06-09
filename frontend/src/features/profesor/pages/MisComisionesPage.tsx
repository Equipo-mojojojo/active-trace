import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '@/shared/services/api'
import type { Comision } from '../types/profesor.types'

/**
 * Home del profesor: grilla de comisiones asignadas.
 * GET /api/v1/analisis/monitor (simplified) — we use asignaciones endpoint if available.
 * For now uses a dedicated comisiones endpoint assumed to be available.
 */
function useComisiones() {
  return useQuery({
    queryKey: ['comisiones'] as const,
    queryFn: async (): Promise<Comision[]> => {
      const { data } = await api.get<Comision[]>('/calificaciones/comisiones')
      return data
    },
  })
}

function ComisionCard({ comision }: { comision: Comision }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="mb-3 flex items-start justify-between">
        <h3 className="font-semibold text-slate-900 leading-tight">
          {comision.materia_nombre}
        </h3>
        <span
          className={[
            'ml-2 inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-medium',
            comision.tiene_calificaciones
              ? 'bg-green-100 text-green-800'
              : 'bg-slate-100 text-slate-600',
          ].join(' ')}
        >
          {comision.tiene_calificaciones ? 'Importado' : 'Sin datos'}
        </span>
      </div>

      <div className="mb-4 space-y-1 text-sm text-slate-500">
        <p>Cohorte: <span className="text-slate-700">{comision.cohorte}</span></p>
        <p>Comisión: <span className="text-slate-700">{comision.comision}</span></p>
        <p>Alumnos: <span className="font-medium text-slate-700">{comision.total_alumnos}</span></p>
      </div>

      <Link
        to={`/profesor/comisiones/${comision.id}`}
        className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-800"
      >
        Ver comisión
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    </div>
  )
}

export function MisComisionesPage() {
  const { data, isLoading, isError } = useComisiones()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <p className="text-slate-500">Cargando comisiones...</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-red-700">Error al cargar las comisiones. Intentá de nuevo más tarde.</p>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <svg
          className="mb-4 h-12 w-12 text-slate-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <h2 className="text-lg font-semibold text-slate-700">Sin comisiones asignadas</h2>
        <p className="mt-1 text-sm text-slate-500">
          No tenés comisiones asignadas para este período.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Mis Comisiones</h1>
        <span className="text-sm text-slate-500">{data.length} comisión{data.length !== 1 ? 'es' : ''}</span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((comision) => (
          <ComisionCard key={comision.id} comision={comision} />
        ))}
      </div>
    </div>
  )
}
