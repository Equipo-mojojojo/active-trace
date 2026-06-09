import type { ActividadDetectada } from '../types/profesor.types'

interface TablaActividadesPreviewProps {
  actividades: ActividadDetectada[]
  seleccionadas: string[]
  onToggle: (nombre: string) => void
}

/**
 * Tabla de actividades detectadas en el archivo subido.
 * Permite seleccionar/deseleccionar cuáles importar.
 */
export function TablaActividadesPreview({
  actividades,
  seleccionadas,
  onToggle,
}: TablaActividadesPreviewProps) {
  const allSelected = actividades.every((a) => seleccionadas.includes(a.nombre))

  const handleToggleAll = () => {
    if (allSelected) {
      actividades.forEach((a) => {
        if (seleccionadas.includes(a.nombre)) onToggle(a.nombre)
      })
    } else {
      actividades.forEach((a) => {
        if (!seleccionadas.includes(a.nombre)) onToggle(a.nombre)
      })
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="w-12 px-4 py-3">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={handleToggleAll}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600"
                aria-label="Seleccionar todas las actividades"
              />
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Actividad
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Tipo
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              Valores de muestra
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {actividades.map((actividad) => (
            <tr key={actividad.nombre} className="hover:bg-slate-50">
              <td className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={seleccionadas.includes(actividad.nombre)}
                  onChange={() => onToggle(actividad.nombre)}
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  aria-label={`Seleccionar actividad ${actividad.nombre}`}
                />
              </td>
              <td className="px-4 py-3 font-medium text-slate-900">{actividad.nombre}</td>
              <td className="px-4 py-3">
                <span
                  className={[
                    'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                    actividad.tipo === 'numerica'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-amber-100 text-amber-800',
                  ].join(' ')}
                >
                  {actividad.tipo === 'numerica' ? 'Numérica' : 'Texto'}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-slate-500">
                {actividad.muestra_valores.slice(0, 3).join(', ')}
                {actividad.muestra_valores.length > 3 && '...'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
