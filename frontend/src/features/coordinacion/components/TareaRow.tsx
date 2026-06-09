/**
 * TareaRow — fila de tarea en la tabla de tareas.
 *
 * Columnas (from Stitch screen 8d5c3c2e698c428ca2dead29ddbaea84):
 *  - Descripción/título
 *  - Asignado a (ID)
 *  - Asignado por (ID)
 *  - Estado (badge semántico)
 *  - Botón "Ver detalle"
 */
import type { Tarea, EstadoTarea } from '../types/coordinacion.types'

interface Props {
  tarea: Tarea
  onVerDetalle: (tarea: Tarea) => void
}

function estadoBadge(estado: EstadoTarea): string {
  const map: Record<EstadoTarea, string> = {
    Pendiente: 'bg-slate-100 text-slate-600',
    'En progreso': 'bg-blue-100 text-blue-700',
    Resuelta: 'bg-green-100 text-green-700',
    Cancelada: 'bg-slate-100 text-slate-400',
  }
  return map[estado]
}

export function TareaRow({ tarea, onVerDetalle }: Props) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3">
        <p className="text-sm font-medium text-slate-900 line-clamp-2">{tarea.descripcion}</p>
      </td>
      <td className="px-4 py-3">
        <p className="text-xs text-slate-500 font-mono">{tarea.asignado_a.slice(0, 8)}…</p>
      </td>
      <td className="px-4 py-3">
        <p className="text-xs text-slate-500 font-mono">{tarea.asignado_por.slice(0, 8)}…</p>
      </td>
      <td className="px-4 py-3">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${estadoBadge(tarea.estado)}`}
        >
          {tarea.estado}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <button
          type="button"
          onClick={() => onVerDetalle(tarea)}
          className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
        >
          Ver detalle
        </button>
      </td>
    </tr>
  )
}
