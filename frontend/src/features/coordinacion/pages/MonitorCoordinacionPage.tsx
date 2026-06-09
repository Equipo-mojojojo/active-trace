/**
 * MonitorCoordinacionPage — monitor institucional transversal (F2.9).
 *
 * Layout (from Stitch screen ff18cb92e45d45df97921bd8ca3ba0dc):
 *  - Filtros horizontales (rango fechas, docente, carrera, estado)
 *  - Botón "Aplicar filtros" / "Limpiar filtros"
 *  - KPI cards (total alumnos, con atrasos, % al día)
 *  - MonitorCoordTable
 */
import { useState } from 'react'
import { useMonitorCoord } from '../hooks/useMonitorCoord'
import { MonitorCoordTable } from '../components/MonitorCoordTable'
import type { MonitorFilters } from '../types/coordinacion.types'

const PAGE_SIZE = 20

const DEFAULT_FILTERS: MonitorFilters = {
  estado: 'todos',
  limit: PAGE_SIZE,
  offset: 0,
}

export function MonitorCoordinacionPage() {
  const [appliedFilters, setAppliedFilters] = useState<MonitorFilters>(DEFAULT_FILTERS)
  const [draftFilters, setDraftFilters] = useState<MonitorFilters>(DEFAULT_FILTERS)
  const [page, setPage] = useState(1)

  const monitorQuery = useMonitorCoord({
    ...appliedFilters,
    offset: (page - 1) * PAGE_SIZE,
  })

  const data = monitorQuery.data
  const entries = data?.entries ?? []
  const total = data?.total ?? 0

  const totalAtrasados = entries.filter((e) => e.atrasado).length
  const pctAlDia = total > 0 ? Math.round(((total - totalAtrasados) / total) * 100) : 0

  const applyFilters = () => {
    setAppliedFilters({ ...draftFilters, limit: PAGE_SIZE })
    setPage(1)
  }

  const clearFilters = () => {
    setDraftFilters(DEFAULT_FILTERS)
    setAppliedFilters(DEFAULT_FILTERS)
    setPage(1)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Monitor Institucional</h1>
        <p className="mt-1 text-sm text-slate-500">
          Vista transversal del estado académico de todos los alumnos
        </p>
      </div>

      {/* Filtros */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Fecha desde</label>
            <input
              type="date"
              value={draftFilters.fecha_desde ?? ''}
              onChange={(e) =>
                setDraftFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Fecha hasta</label>
            <input
              type="date"
              value={draftFilters.fecha_hasta ?? ''}
              onChange={(e) =>
                setDraftFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Docente</label>
            <input
              type="text"
              placeholder="Buscar docente"
              value={draftFilters.docente ?? ''}
              onChange={(e) =>
                setDraftFilters((f) => ({ ...f, docente: e.target.value || undefined }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Estado</label>
            <select
              value={draftFilters.estado ?? 'todos'}
              onChange={(e) =>
                setDraftFilters((f) => ({
                  ...f,
                  estado: e.target.value as MonitorFilters['estado'],
                }))
              }
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="todos">Todos</option>
              <option value="atrasados">Con atrasos</option>
              <option value="al_dia">Al día</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={applyFilters}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Aplicar filtros
            </button>
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Limpiar
            </button>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Total alumnos
          </p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{total}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Con atrasos
          </p>
          <p className="mt-1 text-2xl font-bold text-red-600">{totalAtrasados}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">% Al día</p>
          <p className="mt-1 text-2xl font-bold text-green-600">{pctAlDia}%</p>
        </div>
      </div>

      {/* Tabla */}
      {monitorQuery.isLoading && (
        <p className="text-sm text-slate-500">Cargando datos del monitor...</p>
      )}
      {monitorQuery.isError && (
        <p className="text-sm text-red-600">Error al cargar los datos del monitor.</p>
      )}
      {!monitorQuery.isLoading && (
        <MonitorCoordTable
          entries={entries}
          total={total}
          page={page}
          pageSize={PAGE_SIZE}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  )
}
