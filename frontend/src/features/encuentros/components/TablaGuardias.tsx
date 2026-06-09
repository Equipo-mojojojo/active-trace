/**
 * TablaGuardias — tabla de guardias registradas por tutores.
 */
import type { Guardia } from '../types/encuentros.types'

interface Props {
  guardias: Guardia[]
  onExport: () => void
}

export function TablaGuardias({ guardias, onExport }: Props) {
  if (guardias.length === 0) {
    return (
      <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">No hay guardias registradas con los filtros aplicados.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onExport}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Exportar CSV
        </button>
      </div>
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Docente (asignación)</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Día</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Horario</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Estado</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Comentarios</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {guardias.map((g) => (
              <tr key={g.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <p className="text-xs text-slate-500 font-mono">{g.asignacion_id.slice(0, 8)}…</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-slate-700">{g.dia}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-slate-700">{g.horario}</p>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      g.estado === 'Realizada'
                        ? 'bg-green-100 text-green-700'
                        : g.estado === 'Cancelada'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {g.estado}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-slate-500">{g.comentarios ?? '—'}</p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
