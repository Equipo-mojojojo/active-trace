import type { NotaFinalEntry } from '../types/profesor.types'

interface TablaNotasFinalesProps {
  notas: NotaFinalEntry[]
  actividadesSeleccionadas?: string[]
  onExport?: () => void
}

export function TablaNotasFinales({
  notas,
  actividadesSeleccionadas = [],
  onExport,
}: TablaNotasFinalesProps) {
  if (notas.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-500">No hay notas finales disponibles.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {actividadesSeleccionadas.length > 0 && (
        <p className="text-sm text-slate-500">
          Actividades consideradas:{' '}
          <span className="font-medium">{actividadesSeleccionadas.join(', ')}</span>
        </p>
      )}

      <div className="flex justify-end">
        {onExport && (
          <button
            onClick={onExport}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Exportar CSV
          </button>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                Alumno
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-slate-500">
                Nota final
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {notas.map((entry) => (
              <tr key={entry.entrada_padron_id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {entry.apellidos}, {entry.nombre}
                </td>
                <td className="px-4 py-3 text-right font-semibold text-slate-900">
                  {Number(entry.nota_final).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
