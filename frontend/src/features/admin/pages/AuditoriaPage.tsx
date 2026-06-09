/**
 * AuditoriaPage — Panel de auditoría con métricas.
 *
 * Layout (Stitch: Panel de Auditoría - Administrador):
 *  - Barra de filtros (rango fechas, usuario, acción, materia)
 *  - Card "Acciones por día" (gráfico de barras simple)
 *  - Card "Estado de comunicaciones por docente"
 *  - Card "Interacciones por docente × materia"
 *  - Card "Log completo de auditoría" (tabla)
 *
 * Spec: frontend-auditoria
 * CRITICAL: NEVER send actor_id from frontend. Backend restricts scope from JWT.
 */
import { useState } from 'react'
import {
  useAccionesPorDia,
  useEstadoComunicaciones,
  useInteracciones,
  useUltimasAcciones,
} from '../hooks/useAuditoria'
import type { AuditoriaFilters } from '../types/admin.types'

// actor_id is NEVER in the UI filter state
type UIFilters = Omit<AuditoriaFilters, 'actor_id'>

const ESTADO_COM_COLORS: Record<string, string> = {
  pendiente: 'bg-amber-100 text-amber-800',
  enviando: 'bg-blue-100 text-blue-800',
  enviado: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  cancelado: 'bg-slate-100 text-slate-600',
}

export function AuditoriaPage() {
  const [filters, setFilters] = useState<UIFilters>({})

  const accionesQuery = useAccionesPorDia(filters)
  const comunicacionesQuery = useEstadoComunicaciones(filters)
  const interaccionesQuery = useInteracciones(filters)
  const ultimasQuery = useUltimasAcciones(filters, 200)

  const maxAcciones = Math.max(...(accionesQuery.data ?? []).map((d) => d.total), 1)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Panel de Auditoría</h1>
        <p className="mt-1 text-sm text-slate-500">Métricas de actividad y trazabilidad del tenant</p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label htmlFor="desde" className="mb-1 block text-xs font-medium text-slate-600">Desde</label>
          <input
            id="desde"
            type="date"
            value={filters.desde ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, desde: e.target.value || undefined }))}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label htmlFor="hasta" className="mb-1 block text-xs font-medium text-slate-600">Hasta</label>
          <input
            id="hasta"
            type="date"
            value={filters.hasta ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, hasta: e.target.value || undefined }))}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label htmlFor="accion" className="mb-1 block text-xs font-medium text-slate-600">Acción</label>
          <input
            id="accion"
            type="text"
            placeholder="Ej: importar"
            value={filters.accion ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, accion: e.target.value || undefined }))}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label htmlFor="materia_id" className="mb-1 block text-xs font-medium text-slate-600">Materia ID</label>
          <input
            id="materia_id"
            type="text"
            placeholder="ID de materia"
            value={filters.materia_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Card: Acciones por día */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Acciones por día">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Acciones por día</h2>
        {accionesQuery.isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
        {accionesQuery.data && accionesQuery.data.length === 0 && (
          <p className="py-4 text-center text-sm text-slate-500">Sin actividad en el período seleccionado</p>
        )}
        {accionesQuery.data && accionesQuery.data.length > 0 && (
          <div className="flex items-end gap-1 overflow-x-auto" style={{ height: '120px' }}>
            {accionesQuery.data.map((d) => {
              const pct = Math.max((d.total / maxAcciones) * 100, 4)
              return (
                <div key={d.fecha} className="flex flex-col items-center gap-1 flex-shrink-0">
                  <div
                    className="w-6 rounded-t bg-indigo-500"
                    style={{ height: `${pct}px` }}
                    title={`${d.fecha}: ${d.total}`}
                  />
                  <span className="text-[10px] text-slate-400 rotate-90 origin-center mt-2">{d.fecha.slice(5)}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Card: Estado de comunicaciones */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Estado de comunicaciones">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Estado de comunicaciones por docente</h2>
        {comunicacionesQuery.isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
        {comunicacionesQuery.data && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-slate-500">Docente</th>
                  {['pendiente', 'enviando', 'enviado', 'error', 'cancelado'].map((e) => (
                    <th key={e} className="px-4 py-2 text-center text-xs font-medium uppercase text-slate-500">{e}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {comunicacionesQuery.data.map((d) => (
                  <tr key={d.docente_id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-4 py-2 text-sm text-slate-900">{d.nombre_docente}</td>
                    {(['pendiente', 'enviando', 'enviado', 'error', 'cancelado'] as const).map((e) => (
                      <td key={e} className="whitespace-nowrap px-4 py-2 text-center">
                        {d[e] > 0 ? (
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${ESTADO_COM_COLORS[e]}`}>
                            {d[e]}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-300">0</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
                {comunicacionesQuery.data.length === 0 && (
                  <tr><td colSpan={6} className="py-4 text-center text-sm text-slate-500">Sin datos</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Card: Interacciones */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Interacciones por docente">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Interacciones por docente × materia</h2>
        {interaccionesQuery.isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
        {interaccionesQuery.data && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-slate-500">Docente</th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-slate-500">Materia</th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-slate-500">Acción</th>
                  <th className="px-4 py-2 text-right text-xs font-medium uppercase text-slate-500">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[...(interaccionesQuery.data)].sort((a, b) => b.total - a.total).map((d, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-4 py-2 text-sm text-slate-900">{d.nombre_docente}</td>
                    <td className="whitespace-nowrap px-4 py-2 text-sm text-slate-600">{d.nombre_materia}</td>
                    <td className="whitespace-nowrap px-4 py-2 text-sm text-slate-600">{d.accion}</td>
                    <td className="whitespace-nowrap px-4 py-2 text-right text-sm font-semibold text-slate-900">{d.total}</td>
                  </tr>
                ))}
                {interaccionesQuery.data.length === 0 && (
                  <tr><td colSpan={4} className="py-4 text-center text-sm text-slate-500">Sin datos</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Card: Log completo */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Log completo de auditoría">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Log completo de auditoría</h2>
        {ultimasQuery.isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
        {ultimasQuery.data && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">Fecha/Hora</th>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">Usuario</th>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">Materia</th>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">Acción</th>
                  <th className="px-3 py-2 text-right font-medium uppercase text-slate-500">Registros</th>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">IP</th>
                  <th className="px-3 py-2 text-left font-medium uppercase text-slate-500">User Agent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {ultimasQuery.data.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-3 py-2 text-slate-600">
                      {new Date(a.timestamp).toLocaleString('es-AR')}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-900">{a.nombre_actor}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-600">{a.nombre_materia ?? '—'}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-700">{a.accion}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-right text-slate-700">{a.registros_afectados}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-500 font-mono">{a.ip ?? '—'}</td>
                    <td className="px-3 py-2 text-slate-400 max-w-xs truncate" title={a.user_agent ?? ''}>{a.user_agent ?? '—'}</td>
                  </tr>
                ))}
                {ultimasQuery.data.length === 0 && (
                  <tr><td colSpan={7} className="py-4 text-center text-slate-500">Sin registros</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
