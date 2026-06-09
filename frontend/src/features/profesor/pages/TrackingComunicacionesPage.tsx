import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { TrackingTable } from '../components/TrackingTable'
import { useTrackingComunicaciones } from '../hooks/useTrackingComunicaciones'
import type { EstadoComunicacion } from '../types/profesor.types'

const ESTADOS: Array<{ value: string; label: string }> = [
  { value: '', label: 'Todos' },
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'ENVIANDO', label: 'Enviando' },
  { value: 'OK', label: 'Enviado' },
  { value: 'FALLIDO', label: 'Fallido' },
  { value: 'CANCELADO', label: 'Cancelado' },
]

interface LocationState {
  loteId?: string
}

/**
 * Pantalla de tracking de comunicaciones con polling condicional.
 * Muestra contadores resumen y tabla filtrable por estado.
 */
export function TrackingComunicacionesPage() {
  const location = useLocation()
  const state = location.state as LocationState | undefined
  const loteId = state?.loteId ?? null

  const [filtroEstado, setFiltroEstado] = useState<string>('')
  const { data, isLoading, isError } = useTrackingComunicaciones(loteId)

  const comunicaciones = data?.comunicaciones ?? []

  const contadores = {
    ok: comunicaciones.filter((c) => c.estado === 'OK').length,
    pendiente: comunicaciones.filter(
      (c) => c.estado === 'PENDIENTE' || c.estado === 'ENVIANDO',
    ).length,
    fallido: comunicaciones.filter((c) => c.estado === 'FALLIDO').length,
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Tracking de Comunicaciones</h1>

      {!loteId && (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
          <p className="text-slate-500">
            No hay lote seleccionado. Enviá una comunicación para ver el tracking.
          </p>
        </div>
      )}

      {loteId && (
        <>
          {/* Summary counters */}
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-center">
              <p className="text-2xl font-bold text-green-700">{contadores.ok}</p>
              <p className="text-sm text-green-600">Enviados</p>
            </div>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-center">
              <p className="text-2xl font-bold text-amber-700">{contadores.pendiente}</p>
              <p className="text-sm text-amber-600">Pendientes</p>
            </div>
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
              <p className="text-2xl font-bold text-red-700">{contadores.fallido}</p>
              <p className="text-sm text-red-600">Fallidos</p>
            </div>
          </div>

          {/* Filter */}
          <div className="flex items-center gap-3">
            <label htmlFor="filtro-estado" className="text-sm font-medium text-slate-700">
              Filtrar por estado:
            </label>
            <select
              id="filtro-estado"
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ESTADOS.map((e) => (
                <option key={e.value} value={e.value}>
                  {e.label}
                </option>
              ))}
            </select>

            {contadores.pendiente > 0 && (
              <span className="text-xs text-slate-400 animate-pulse">
                Actualizando cada 5s...
              </span>
            )}
          </div>

          {isLoading && (
            <p className="text-sm text-slate-500">Cargando comunicaciones...</p>
          )}

          {isError && (
            <p className="text-sm text-red-600">
              Error al cargar el tracking. Reintentando...
            </p>
          )}

          {data && (
            <TrackingTable
              comunicaciones={comunicaciones}
              filtroEstado={filtroEstado as EstadoComunicacion | ''}
            />
          )}
        </>
      )}
    </div>
  )
}
