/**
 * TablaEncuentros — tabla global de slots de encuentros.
 *
 * Columnas:
 *  - Materia (materia_id)
 *  - Tipo (Recurrente/Único)
 *  - Día/Hora o Fecha única
 *  - Meet URL
 *  - Estado vigencia
 *  - Acciones (Ver instancias)
 */
import type { SlotEncuentro } from '../types/encuentros.types'

interface Props {
  slots: SlotEncuentro[]
  onVerInstancias: (slot: SlotEncuentro) => void
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function TablaEncuentros({ slots, onVerInstancias }: Props) {
  if (slots.length === 0) {
    return (
      <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">No hay encuentros registrados.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-100">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Título</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Tipo</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Horario</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Meet URL</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Vigencia</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {slots.map((slot) => {
            const isUnico = slot.cant_semanas === 0 && slot.fecha_unica
            return (
              <tr key={slot.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-slate-900">{slot.titulo}</p>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      isUnico
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-indigo-100 text-indigo-700'
                    }`}
                  >
                    {isUnico ? 'Único' : 'Recurrente'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {isUnico ? (
                    <p className="text-sm text-slate-600">
                      {formatDate(slot.fecha_unica!)} {slot.hora}
                    </p>
                  ) : (
                    <p className="text-sm text-slate-600">
                      {slot.dia_semana} {slot.hora}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3">
                  {slot.meet_url ? (
                    <a
                      href={slot.meet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-indigo-600 hover:underline truncate max-w-32 block"
                    >
                      {slot.meet_url}
                    </a>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <p className="text-xs text-slate-500">
                    {formatDate(slot.vig_desde)}
                    {slot.vig_hasta ? ` — ${formatDate(slot.vig_hasta)}` : ''}
                  </p>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => onVerInstancias(slot)}
                    className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    Ver instancias
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
