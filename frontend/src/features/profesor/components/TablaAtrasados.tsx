import type { AlumnoAtrasado } from '../types/profesor.types'

interface TablaAtrasadosProps {
  atrasados: AlumnoAtrasado[]
  seleccionados: string[]
  onToggleSeleccion: (id: string) => void
  onComunicar?: () => void
}

/**
 * Tabla de alumnos atrasados con selección por checkbox.
 * Columnas: Alumno, Legajo, Actividades faltantes, Nota promedio, Estado.
 */
export function TablaAtrasados({
  atrasados,
  seleccionados,
  onToggleSeleccion,
  onComunicar,
}: TablaAtrasadosProps) {
  if (atrasados.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-500">No hay alumnos atrasados en esta comisión.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {seleccionados.length > 0 && onComunicar && (
        <div className="flex items-center justify-between rounded-md bg-indigo-50 px-4 py-2">
          <span className="text-sm text-indigo-700">
            {seleccionados.length} alumno{seleccionados.length > 1 ? 's' : ''} seleccionado
            {seleccionados.length > 1 ? 's' : ''}
          </span>
          <button
            onClick={onComunicar}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Comunicar seleccionados
          </button>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="w-12 px-4 py-3" />
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                Alumno
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                Comisión
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                Actividades faltantes
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wide text-slate-500">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {atrasados.map((alumno) => (
              <tr
                key={alumno.entrada_padron_id}
                className="hover:bg-slate-50"
                data-testid="atrasado-row"
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={seleccionados.includes(alumno.entrada_padron_id)}
                    onChange={() => onToggleSeleccion(alumno.entrada_padron_id)}
                    className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    aria-label={`Seleccionar ${alumno.nombre} ${alumno.apellidos}`}
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">
                    {alumno.apellidos}, {alumno.nombre}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">
                  {alumno.comision ?? '—'}
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">
                  {alumno.actividades_faltantes.length > 0
                    ? alumno.actividades_faltantes.join(', ')
                    : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                    Atrasado
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
