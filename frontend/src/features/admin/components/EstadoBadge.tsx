import type { EstadoEntidad } from '../types/admin.types'

interface EstadoBadgeProps {
  estado: EstadoEntidad
}

export function EstadoBadge({ estado }: EstadoBadgeProps) {
  const colorClass = estado === 'Activa'
    ? 'bg-green-100 text-green-800'
    : 'bg-slate-100 text-slate-600'

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
      {estado}
    </span>
  )
}
