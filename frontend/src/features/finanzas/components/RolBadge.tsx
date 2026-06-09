import type { RolDocente } from '../types/finanzas.types'

const ROL_COLORS: Record<string, string> = {
  PROFESOR: 'bg-blue-100 text-blue-800',
  TUTOR: 'bg-purple-100 text-purple-800',
  COORDINADOR: 'bg-indigo-100 text-indigo-800',
  NEXO: 'bg-teal-100 text-teal-800',
  ADMIN: 'bg-slate-100 text-slate-800',
  FINANZAS: 'bg-green-100 text-green-800',
}

interface RolBadgeProps {
  rol: RolDocente | string
}

export function RolBadge({ rol }: RolBadgeProps) {
  const colorClass = ROL_COLORS[rol] ?? 'bg-slate-100 text-slate-800'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
      {rol}
    </span>
  )
}
