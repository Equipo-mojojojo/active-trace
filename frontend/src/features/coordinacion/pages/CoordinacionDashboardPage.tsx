/**
 * Dashboard de Coordinación — home del COORDINADOR/ADMIN.
 *
 * Layout (from Stitch screen 7ae121f3705a46f392937e7c3fea7d34):
 *  - 4 cards de acceso rápido (Equipos, Avisos, Tareas, Monitor)
 *  - Sección "Tareas pendientes" — lista de mis tareas con badge de estado
 *  - Sección "Avisos activos" — últimos avisos con badge de severidad
 */
import { Link } from 'react-router-dom'
import { useTareas } from '../hooks/useTareas'
import { useAvisos } from '../hooks/useAvisos'
import type { EstadoTarea, SeveridadAviso } from '../types/coordinacion.types'

const QUICK_ACCESS = [
  {
    title: 'Equipos Docentes',
    description: 'Gestionar asignaciones y equipos',
    path: '/coordinacion/equipos',
    color: 'bg-indigo-50 border-indigo-200',
    iconColor: 'text-indigo-600',
  },
  {
    title: 'Avisos',
    description: 'Publicar avisos institucionales',
    path: '/coordinacion/avisos',
    color: 'bg-amber-50 border-amber-200',
    iconColor: 'text-amber-600',
  },
  {
    title: 'Tareas',
    description: 'Gestionar tareas del equipo',
    path: '/coordinacion/tareas',
    color: 'bg-emerald-50 border-emerald-200',
    iconColor: 'text-emerald-600',
  },
  {
    title: 'Monitor Institucional',
    description: 'Ver estado académico global',
    path: '/coordinacion/monitor',
    color: 'bg-sky-50 border-sky-200',
    iconColor: 'text-sky-600',
  },
]

function estadoBadge(estado: EstadoTarea) {
  const map: Record<EstadoTarea, string> = {
    Pendiente: 'bg-slate-100 text-slate-700',
    'En progreso': 'bg-blue-100 text-blue-700',
    Resuelta: 'bg-green-100 text-green-700',
    Cancelada: 'bg-slate-100 text-slate-400',
  }
  return map[estado]
}

function severidadBadge(sev: SeveridadAviso) {
  const map: Record<SeveridadAviso, string> = {
    Info: 'bg-blue-100 text-blue-700',
    Advertencia: 'bg-amber-100 text-amber-700',
    Crítico: 'bg-red-100 text-red-700',
  }
  return map[sev]
}

export function CoordinacionDashboardPage() {
  const tareasQuery = useTareas('mias')
  const avisosQuery = useAvisos()

  const tareasActivas = (tareasQuery.data ?? []).filter(
    (t) => t.estado !== 'Resuelta' && t.estado !== 'Cancelada',
  )
  const avisosActivos = (avisosQuery.data ?? []).filter((a) => a.activo).slice(0, 5)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Panel de Coordinación</h1>
        <p className="mt-1 text-sm text-slate-500">
          Bienvenido. Desde aquí podés gestionar equipos, avisos, tareas y ver el monitor
          institucional.
        </p>
      </div>

      {/* Quick access cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {QUICK_ACCESS.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`block rounded-lg border p-6 transition-shadow hover:shadow-md ${item.color}`}
          >
            <p className={`text-sm font-medium ${item.iconColor}`}>{item.title}</p>
            <p className="mt-1 text-xs text-slate-500">{item.description}</p>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Tareas pendientes */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Mis tareas pendientes</h2>
            <Link
              to="/coordinacion/tareas"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              Ver todas
            </Link>
          </div>

          {tareasQuery.isLoading && (
            <p className="text-sm text-slate-400">Cargando...</p>
          )}
          {tareasQuery.isError && (
            <p className="text-sm text-red-600">Error al cargar tareas</p>
          )}
          {!tareasQuery.isLoading && tareasActivas.length === 0 && (
            <p className="text-sm text-slate-400">No tenés tareas pendientes.</p>
          )}
          <ul className="space-y-3">
            {tareasActivas.slice(0, 5).map((tarea) => (
              <li
                key={tarea.id}
                className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2"
              >
                <p className="text-sm text-slate-700 line-clamp-1">{tarea.descripcion}</p>
                <span
                  className={`ml-3 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${estadoBadge(tarea.estado)}`}
                >
                  {tarea.estado}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Avisos activos */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Avisos activos</h2>
            <Link
              to="/coordinacion/avisos"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              Ver todos
            </Link>
          </div>

          {avisosQuery.isLoading && (
            <p className="text-sm text-slate-400">Cargando...</p>
          )}
          {avisosQuery.isError && (
            <p className="text-sm text-red-600">Error al cargar avisos</p>
          )}
          {!avisosQuery.isLoading && avisosActivos.length === 0 && (
            <p className="text-sm text-slate-400">No hay avisos activos.</p>
          )}
          <ul className="space-y-3">
            {avisosActivos.map((aviso) => (
              <li
                key={aviso.id}
                className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2"
              >
                <p className="text-sm text-slate-700 line-clamp-1">{aviso.titulo}</p>
                <span
                  className={`ml-3 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${severidadBadge(aviso.severidad)}`}
                >
                  {aviso.severidad}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
