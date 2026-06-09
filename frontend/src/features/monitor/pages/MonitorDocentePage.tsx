import { useState } from 'react'
import { FiltrosMonitor } from '../components/FiltrosMonitor'
import { TablaMonitor } from '../components/TablaMonitor'
import { useMonitor } from '../hooks/useMonitor'
import type { MonitorFiltros } from '@/features/profesor/types/profesor.types'

/**
 * Monitor de seguimiento de alumnos (F2.8).
 * Para TUTOR y PROFESOR. Tabla filtrable con debounce 300ms.
 */
export function MonitorDocentePage() {
  const [filtros, setFiltros] = useState<MonitorFiltros>({})
  const { data, isLoading, isError } = useMonitor(filtros)

  const entries = data?.entries ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Monitor de Seguimiento</h1>
        {data && (
          <span className="text-sm text-slate-500">
            {data.total} alumno{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <FiltrosMonitor filtros={filtros} onChange={setFiltros} />
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <p className="text-sm text-slate-500">Cargando monitor...</p>
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            Error al cargar el monitor. Intentá de nuevo más tarde.
          </p>
        </div>
      )}

      {!isLoading && !isError && entries.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-slate-500">No hay alumnos que coincidan con los filtros aplicados.</p>
          <p className="mt-1 text-sm text-slate-400">
            Intentá con otros parámetros de búsqueda.
          </p>
        </div>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <TablaMonitor entries={entries} />
      )}
    </div>
  )
}
