/**
 * ConvocatoriaCard — card de convocatoria de coloquio.
 *
 * Diseño (from Stitch screen e3031247af39418b8a8788b1323af8f2):
 *  - Materia ID + instancia (badge)
 *  - Métricas horizontales (Convocados/Reservas/Libres)
 *  - Estado badge (Abierta=verde/Cerrada=gris)
 *  - Botón "Ver detalle"
 */
import type { Convocatoria } from '../types/coloquios.types'
import { useConvocatoriaMetricas } from '../hooks/useColoquios'

interface Props {
  convocatoria: Convocatoria
  onVerDetalle: (conv: Convocatoria) => void
}

function estadoBadge(estado: string) {
  return estado === 'Abierta'
    ? 'bg-green-100 text-green-700'
    : 'bg-slate-100 text-slate-500'
}

export function ConvocatoriaCard({ convocatoria, onVerDetalle }: Props) {
  const metricasQuery = useConvocatoriaMetricas(convocatoria.id)
  const metricas = metricasQuery.data

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        {/* Left */}
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900">
              Materia: {convocatoria.materia_id.slice(0, 8)}…
            </p>
            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
              {convocatoria.instancia}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${estadoBadge(convocatoria.estado)}`}
            >
              {convocatoria.estado}
            </span>
          </div>

          <p className="text-xs text-slate-500">
            Tipo: {convocatoria.tipo} — Días disponibles: {convocatoria.dias_disponibles}
          </p>

          {/* Métricas */}
          {metricas && (
            <div className="flex gap-6 text-xs">
              <div>
                <p className="text-slate-400">Convocados</p>
                <p className="font-semibold text-slate-700">{metricas.convocados}</p>
              </div>
              <div>
                <p className="text-slate-400">Reservas</p>
                <p className="font-semibold text-slate-700">{metricas.reservas}</p>
              </div>
              <div>
                <p className="text-slate-400">Libres</p>
                <p className="font-semibold text-slate-700">{metricas.libres}</p>
              </div>
            </div>
          )}
          {metricasQuery.isLoading && (
            <p className="text-xs text-slate-400">Cargando métricas...</p>
          )}
        </div>

        {/* Action */}
        <button
          type="button"
          onClick={() => onVerDetalle(convocatoria)}
          className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          Ver detalle
        </button>
      </div>
    </div>
  )
}
