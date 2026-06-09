import type { MonitorEntry } from '@/features/profesor/types/profesor.types'

interface TablaMonitorProps {
  entries: MonitorEntry[]
}

/**
 * Tabla del monitor de seguimiento.
 * Columnas: Alumno, Comisión, Actividades cumplidas (%), Estado.
 */
export function TablaMonitor({ entries }: TablaMonitorProps) {
  if (entries.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-500">No se encontraron alumnos con los filtros actuales.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Alumno
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Comisión
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-slate-500">
              Aprobadas
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-slate-500">
              Faltantes
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wide text-slate-500">
              Estado
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {entries.map((entry) => {
            const total = entry.aprobadas + entry.reprobadas + entry.faltantes
            const pct = total > 0 ? Math.round((entry.aprobadas / total) * 100) : 0

            return (
              <tr key={entry.entrada_padron_id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">
                    {entry.apellidos}, {entry.nombre}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">
                  {entry.comision ?? '—'}
                </td>
                <td className="px-4 py-3 text-right text-sm text-slate-900">
                  {entry.aprobadas} ({pct}%)
                </td>
                <td className="px-4 py-3 text-right text-sm text-slate-600">
                  {entry.faltantes}
                </td>
                <td className="px-4 py-3 text-center">
                  {entry.atrasado ? (
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                      Atrasado
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                      Al día
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
