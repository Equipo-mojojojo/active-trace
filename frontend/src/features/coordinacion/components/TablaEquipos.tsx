/**
 * TablaEquipos — tabla principal de asignaciones docentes.
 *
 * Columnas (from Stitch screen 9368f556d4584ff4a0cae673ca93eb4e):
 *  - Docente (nombre)
 *  - Rol (badge con color)
 *  - Materias/Comisiones (texto)
 *  - Vigencia desde/hasta
 *  - Estado (Vigente=verde, Vencida=gris, Futura=azul)
 *  - Acciones (Editar, Eliminar)
 */
import type { Asignacion, EstadoVigencia } from '../types/coordinacion.types'

interface Props {
  asignaciones: Asignacion[]
  onEdit: (asignacion: Asignacion) => void
  onDelete: (id: string) => void
  isDeleting?: string | null
}

const ROL_COLORS: Record<string, string> = {
  TUTOR: 'bg-indigo-100 text-indigo-700',
  PROFESOR: 'bg-emerald-100 text-emerald-700',
  COORDINADOR: 'bg-purple-100 text-purple-700',
  NEXO: 'bg-sky-100 text-sky-700',
}

function rolBadge(rol: string) {
  return ROL_COLORS[rol.toUpperCase()] ?? 'bg-slate-100 text-slate-700'
}

function estadoBadge(estado: EstadoVigencia) {
  const map: Record<EstadoVigencia, string> = {
    Vigente: 'bg-green-100 text-green-700',
    Vencida: 'bg-slate-100 text-slate-500',
    Futura: 'bg-blue-100 text-blue-700',
  }
  return map[estado]
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function TablaEquipos({ asignaciones, onEdit, onDelete, isDeleting }: Props) {
  if (asignaciones.length === 0) {
    return (
      <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm text-slate-500">
          No hay asignaciones con los filtros seleccionados.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-100">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Docente</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Comisiones</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Vigencia</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Estado</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {asignaciones.map((asig) => (
            <tr key={asig.id} className="hover:bg-slate-50">
              <td className="px-4 py-3">
                <p className="text-sm font-medium text-slate-900">
                  {asig.nombre_usuario ?? 'Docente sin nombre'}
                </p>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${rolBadge(asig.rol)}`}
                >
                  {asig.rol}
                </span>
              </td>
              <td className="px-4 py-3">
                <p className="text-sm text-slate-600">{asig.comisiones ?? '—'}</p>
              </td>
              <td className="px-4 py-3">
                <p className="text-xs text-slate-500">
                  {formatDate(asig.desde)} — {formatDate(asig.hasta)}
                </p>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${estadoBadge(asig.estado_vigencia)}`}
                >
                  {asig.estado_vigencia}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => onEdit(asig)}
                    className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(asig.id)}
                    disabled={isDeleting === asig.id}
                    className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-40"
                  >
                    {isDeleting === asig.id ? 'Eliminando...' : 'Eliminar'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
