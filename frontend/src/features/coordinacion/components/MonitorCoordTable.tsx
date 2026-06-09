/**
 * MonitorCoordTable — tabla del monitor institucional (F2.9).
 *
 * Columnas (from Stitch screen ff18cb92e45d45df97921bd8ca3ba0dc):
 *  - Alumno (nombre + apellidos)
 *  - Comisión
 *  - Docente (regional)
 *  - Actividades aprobadas (barra de progreso + texto N/Total)
 *  - Actividades faltantes (badge rojo)
 *  - Estado (badge semántico: Al día=verde, Atrasado=rojo)
 *  - Paginación
 */
import type { MonitorAlumno } from '../types/coordinacion.types'

interface Props {
  entries: MonitorAlumno[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
}

function estadoBadge(atrasado: boolean) {
  return atrasado
    ? 'bg-red-100 text-red-700'
    : 'bg-green-100 text-green-700'
}

function ProgressBar({ aprobadas, total }: { aprobadas: number; total: number }) {
  const pct = total > 0 ? Math.round((aprobadas / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-indigo-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-500">
        {aprobadas}/{total}
      </span>
    </div>
  )
}

export function MonitorCoordTable({ entries, total, page, pageSize, onPageChange }: Props) {
  const totalPages = Math.ceil(total / pageSize)
  const from = (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, total)

  if (entries.length === 0) {
    return (
      <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">No se encontraron alumnos con los filtros aplicados.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Alumno</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Comisión</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Regional</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                Aprobadas
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                Faltantes
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {entries.map((entry) => {
              const totalActs = entry.aprobadas + entry.reprobadas + entry.faltantes
              return (
                <tr key={entry.entrada_padron_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-slate-900">
                      {entry.nombre} {entry.apellidos}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm text-slate-600">{entry.comision ?? '—'}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm text-slate-600">{entry.regional ?? '—'}</p>
                  </td>
                  <td className="px-4 py-3">
                    <ProgressBar aprobadas={entry.aprobadas} total={totalActs} />
                  </td>
                  <td className="px-4 py-3">
                    {entry.faltantes > 0 ? (
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-xs font-semibold text-red-700">
                        {entry.faltantes}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${estadoBadge(entry.atrasado)}`}
                    >
                      {entry.atrasado ? 'Atrasado' : 'Al día'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>
            Mostrando {from}–{to} de {total}
          </span>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50 disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              type="button"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50 disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
