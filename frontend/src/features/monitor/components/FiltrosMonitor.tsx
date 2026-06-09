import { useState } from 'react'
import type { MonitorFiltros } from '@/features/profesor/types/profesor.types'

interface FiltrosMonitorProps {
  filtros: MonitorFiltros
  onChange: (filtros: MonitorFiltros) => void
}

/**
 * Filtros para el monitor de seguimiento.
 * La búsqueda por alumno tiene debounce de 300ms (gestionado en useMonitor).
 */
export function FiltrosMonitor({ filtros, onChange }: FiltrosMonitorProps) {
  const [q, setQ] = useState(filtros.q ?? '')

  const handleQChange = (value: string) => {
    setQ(value)
    onChange({ ...filtros, q: value })
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <label htmlFor="monitor-q" className="mb-1 block text-xs font-medium text-slate-700">
          Buscar alumno
        </label>
        <input
          id="monitor-q"
          type="text"
          value={q}
          onChange={(e) => handleQChange(e.target.value)}
          placeholder="Nombre o correo..."
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label htmlFor="monitor-comision" className="mb-1 block text-xs font-medium text-slate-700">
          Comisión
        </label>
        <input
          id="monitor-comision"
          type="text"
          value={filtros.comision ?? ''}
          onChange={(e) => onChange({ ...filtros, comision: e.target.value || undefined })}
          placeholder="Ej: A, B..."
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label htmlFor="monitor-min" className="mb-1 block text-xs font-medium text-slate-700">
          Mínimo aprobadas
        </label>
        <input
          id="monitor-min"
          type="number"
          min={0}
          value={filtros.min_aprobadas ?? ''}
          onChange={(e) =>
            onChange({
              ...filtros,
              min_aprobadas: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          placeholder="Ej: 5"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="flex items-end">
        <button
          onClick={() => {
            setQ('')
            onChange({})
          }}
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Limpiar filtros
        </button>
      </div>
    </div>
  )
}
