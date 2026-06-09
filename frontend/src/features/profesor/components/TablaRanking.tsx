import type { RankingEntry } from '../types/profesor.types'

interface TablaRankingProps {
  ranking: RankingEntry[]
}

export function TablaRanking({ ranking }: TablaRankingProps) {
  if (ranking.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-500">No hay datos de ranking disponibles.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="w-16 px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              #
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Alumno
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Comisión
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-slate-500">
              Actividades aprobadas
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {ranking.map((entry, idx) => (
            <tr key={entry.entrada_padron_id} className="hover:bg-slate-50">
              <td className="px-4 py-3 text-sm font-semibold text-slate-700">{idx + 1}</td>
              <td className="px-4 py-3 font-medium text-slate-900">
                {entry.apellidos}, {entry.nombre}
              </td>
              <td className="px-4 py-3 text-sm text-slate-600">{entry.comision ?? '—'}</td>
              <td className="px-4 py-3 text-right">
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                  {entry.aprobadas}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
