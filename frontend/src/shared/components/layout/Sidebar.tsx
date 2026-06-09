import { NavLink } from 'react-router-dom'
import { usePermission } from '@/shared/hooks/usePermission'

interface NavItem {
  label: string
  path: string
  /** Single permission string, or array (OR logic — visible if user has ANY). Empty string = always visible. */
  permission: string | string[]
  icon: string
}

/**
 * Navigation items — each requires a permission to be visible.
 * Permissions must match exactly what's in the DB (see seed_dev.py _ROLE_PERMISSIONS).
 * Spec: frontend-routing §"Menú dinámico"
 */
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', permission: '', icon: '' },
  // Visible to PROFESOR (propio) and COORDINADOR/ADMIN (full)
  { label: 'Mis Avisos', path: '/profesor/avisos', permission: 'aviso:ack', icon: '' },
  { label: 'Mis Comisiones', path: '/profesor/comisiones', permission: ['atrasados:ver:propio', 'atrasados:ver'], icon: '' },
  { label: 'Monitor', path: '/monitor', permission: ['atrasados:ver:propio', 'atrasados:ver'], icon: '' },
  // ── C-23 Coordinación ──────────────────────────────────────────────────────
  { label: '— Coordinación —', path: '#', permission: 'equipos:asignar', icon: '' },
  { label: 'Equipos Docentes', path: '/coordinacion/equipos', permission: 'equipos:asignar', icon: '' },
  { label: 'Avisos', path: '/coordinacion/avisos', permission: 'avisos:publicar', icon: '' },
  { label: 'Tareas', path: '/coordinacion/tareas', permission: ['tareas:gestionar', 'tareas:gestionar:propio'], icon: '' },
  { label: 'Monitor Institucional', path: '/coordinacion/monitor', permission: 'atrasados:ver', icon: '' },
  { label: 'Encuentros', path: '/encuentros', permission: ['encuentros:gestionar', 'encuentros:gestionar:propio'], icon: '' },
  { label: 'Guardias', path: '/encuentros/guardias', permission: ['guardias:registrar', 'guardias:registrar:propio'], icon: '' },
  { label: 'Coloquios', path: '/coloquios', permission: 'equipos:asignar', icon: '' },
  // ── C-24 Finanzas ─────────────────────────────────────────────────────────
  { label: '— Finanzas —', path: '#', permission: 'liquidaciones:operar', icon: '' },
  { label: 'Grilla Salarial', path: '/finanzas/grilla-salarial', permission: 'liquidaciones:operar', icon: '' },
  { label: 'Liquidaciones', path: '/finanzas/liquidaciones', permission: 'liquidaciones:cerrar', icon: '' },
  { label: 'Facturas', path: '/finanzas/facturas', permission: 'facturas:gestionar', icon: '' },
  // ── C-24 Administración ───────────────────────────────────────────────────
  { label: '— Administración —', path: '#', permission: 'estructura:gestionar', icon: '' },
  { label: 'Estructura Académica', path: '/admin/estructura', permission: 'estructura:gestionar', icon: '' },
  { label: 'Usuarios', path: '/admin/usuarios', permission: 'usuarios:gestionar', icon: '' },
  // Auditoría: visible to ADMIN (auditoria:ver) and FINANZAS (auditoria:ver) — same permission
  { label: 'Auditoría', path: '/admin/auditoria', permission: 'auditoria:ver', icon: '' },
]

export function Sidebar() {
  const { hasPermission } = usePermission()

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.permission === '') return true
    if (Array.isArray(item.permission)) return item.permission.some((p) => hasPermission(p))
    return hasPermission(item.permission)
  })

  return (
    <nav
      aria-label="Navegación principal"
      className="flex h-full w-64 flex-col bg-slate-900 px-4 py-6"
    >
      {/* Brand */}
      <div className="mb-8 px-2">
        <span className="text-xl font-bold text-white">active-trace</span>
      </div>

      {/* Nav items */}
      <ul className="flex-1 space-y-1" role="list">
        {visibleItems.map((item) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
