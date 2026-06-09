import { useNavigate } from 'react-router-dom'
import { usePermission } from '@/shared/hooks/usePermission'
import { useAuth } from '@/shared/hooks/useAuth'

interface DashboardCard {
  title: string
  description: string
  path: string
  permission: string | string[]
}

const CARDS: DashboardCard[] = [
  // Académico — Profesor
  {
    title: 'Mis Avisos',
    description: 'Avisos institucionales publicados para tu rol.',
    path: '/profesor/avisos',
    permission: 'aviso:ack',
  },
  {
    title: 'Mis Comisiones',
    description: 'Revisá el estado de tus comisiones, alumnos atrasados y entregas pendientes.',
    path: '/profesor/comisiones',
    permission: ['atrasados:ver:propio', 'atrasados:ver'],
  },
  {
    title: 'Monitor',
    description: 'Seguimiento en tiempo real de actividad académica de tus comisiones.',
    path: '/monitor',
    permission: ['atrasados:ver:propio', 'atrasados:ver'],
  },
  // Coordinación
  {
    title: 'Equipos Docentes',
    description: 'Gestioná las asignaciones de docentes por materia y comisión.',
    path: '/coordinacion/equipos',
    permission: 'equipos:asignar',
  },
  {
    title: 'Avisos',
    description: 'Publicá avisos institucionales para alumnos y docentes.',
    path: '/coordinacion/avisos',
    permission: 'avisos:publicar',
  },
  {
    title: 'Tareas',
    description: 'Gestioná tareas internas del equipo docente.',
    path: '/coordinacion/tareas',
    permission: ['tareas:gestionar', 'tareas:gestionar:propio'],
  },
  {
    title: 'Monitor Institucional',
    description: 'Vista global del seguimiento académico de todas las comisiones.',
    path: '/coordinacion/monitor',
    permission: 'atrasados:ver',
  },
  {
    title: 'Encuentros',
    description: 'Planificá y registrá encuentros de las comisiones.',
    path: '/encuentros',
    permission: ['encuentros:gestionar', 'encuentros:gestionar:propio'],
  },
  {
    title: 'Guardias',
    description: 'Registrá guardias y turnos del equipo docente.',
    path: '/encuentros/guardias',
    permission: ['guardias:registrar', 'guardias:registrar:propio'],
  },
  // Finanzas
  {
    title: 'Grilla Salarial',
    description: 'Configurá la grilla de salarios base y adicionales.',
    path: '/finanzas/grilla-salarial',
    permission: 'liquidaciones:operar',
  },
  {
    title: 'Liquidaciones',
    description: 'Calculá y cerrá liquidaciones de honorarios docentes.',
    path: '/finanzas/liquidaciones',
    permission: 'liquidaciones:cerrar',
  },
  {
    title: 'Facturas',
    description: 'Gestioná facturas asociadas a liquidaciones y honorarios.',
    path: '/finanzas/facturas',
    permission: 'facturas:gestionar',
  },
  // Admin
  {
    title: 'Estructura Académica',
    description: 'Administrá carreras, cohortes y materias del tenant.',
    path: '/admin/estructura',
    permission: 'estructura:gestionar',
  },
  {
    title: 'Usuarios',
    description: 'Gestioná usuarios, roles y permisos del tenant.',
    path: '/admin/usuarios',
    permission: 'usuarios:gestionar',
  },
  {
    title: 'Auditoría',
    description: 'Revisá el registro completo de acciones y cambios en el sistema.',
    path: '/admin/auditoria',
    permission: 'auditoria:ver',
  },
]

export function DashboardPage() {
  const { hasPermission } = usePermission()
  const { user } = useAuth()
  const navigate = useNavigate()

  const visibleCards = CARDS.filter((card) =>
    Array.isArray(card.permission)
      ? card.permission.some((p) => hasPermission(p))
      : hasPermission(card.permission),
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Bienvenido{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Desde acá accedés a todas las secciones habilitadas para tu rol.
        </p>
      </div>

      {visibleCards.length === 0 ? (
        <p className="text-sm text-slate-400">No tenés accesos configurados todavía.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visibleCards.map((card) => (
            <button
              key={card.path}
              onClick={() => navigate(card.path)}
              className="group rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition-all hover:border-indigo-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <h2 className="text-sm font-semibold text-slate-800 group-hover:text-indigo-700">
                {card.title}
              </h2>
              <p className="mt-1.5 text-xs leading-relaxed text-slate-500">{card.description}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
