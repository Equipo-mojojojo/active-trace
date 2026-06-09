import type { ComunicacionEstado, EstadoComunicacion } from '../types/profesor.types'

interface TrackingTableProps {
  comunicaciones: ComunicacionEstado[]
  filtroEstado: string
}

const ESTADO_BADGES: Record<EstadoComunicacion, { label: string; className: string }> = {
  PENDIENTE: { label: 'Pendiente', className: 'bg-amber-100 text-amber-800' },
  ENVIANDO: { label: 'Enviando', className: 'bg-blue-100 text-blue-800' },
  OK: { label: 'Enviado', className: 'bg-green-100 text-green-800' },
  FALLIDO: { label: 'Fallido', className: 'bg-red-100 text-red-800' },
  CANCELADO: { label: 'Cancelado', className: 'bg-slate-100 text-slate-600' },
}

/**
 * Tabla de comunicaciones con badges semánticos de estado.
 * Verde=OK, Amarillo=Pendiente, Rojo=Fallido, Gris=Cancelado/Enviando.
 */
export function TrackingTable({ comunicaciones, filtroEstado }: TrackingTableProps) {
  const filtered = filtroEstado
    ? comunicaciones.filter((c) => c.estado === filtroEstado)
    : comunicaciones

  if (filtered.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-500">No hay comunicaciones{filtroEstado ? ' con ese estado' : ''}.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Destinatario
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wide text-slate-500">
              Estado
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Detalle
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filtered.map((com) => {
            const badge = ESTADO_BADGES[com.estado as EstadoComunicacion] ?? {
              label: com.estado,
              className: 'bg-slate-100 text-slate-600',
            }

            return (
              <tr key={com.id} className="hover:bg-slate-50" data-testid="tracking-row">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {com.destinatario_nombre}
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}
                  >
                    {badge.label}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-slate-500">
                  {com.error_detalle ?? '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
