import type { RolUsuario } from '../types/admin.types'

const ROL_COLORS: Record<string, string> = {
  ADMIN: 'bg-slate-800 text-white',
  COORDINADOR: 'bg-indigo-100 text-indigo-800',
  PROFESOR: 'bg-blue-100 text-blue-800',
  TUTOR: 'bg-purple-100 text-purple-800',
  NEXO: 'bg-teal-100 text-teal-800',
  FINANZAS: 'bg-green-100 text-green-800',
  ALUMNO: 'bg-amber-100 text-amber-800',
}

interface RolBadgeAdminProps {
  rol: RolUsuario | string
}

export function RolBadgeAdmin({ rol }: RolBadgeAdminProps) {
  const colorClass = ROL_COLORS[rol] ?? 'bg-slate-100 text-slate-800'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
      {rol}
    </span>
  )
}
