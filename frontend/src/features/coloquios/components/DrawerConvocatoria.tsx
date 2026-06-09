/**
 * DrawerConvocatoria — panel tabbed con 3 tabs para gestión de convocatoria.
 *
 * Tabs (from Stitch screen e3031247af39418b8a8788b1323af8f2):
 *  1. Alumnos convocados (tabla + import desde archivo)
 *  2. Reservas (tabla con badges)
 *  3. Resultados (tabla con campos editables)
 *
 * Max ~180 LOC — componentes de tabla simples inline para mantener < 200 LOC.
 */
import { useState } from 'react'
import { useReservas, useResultados, useSaveResultado, useCerrarConvocatoria } from '../hooks/useColoquios'
import { coloquiosService } from '../services/coloquiosService'
import type { Convocatoria, Convocado } from '../types/coloquios.types'

type Tab = 'convocados' | 'reservas' | 'resultados'

interface Props {
  convocatoria: Convocatoria | null
  convocados: Convocado[]
  open: boolean
  onClose: () => void
}

export function DrawerConvocatoria({ convocatoria, convocados, open, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('convocados')
  const [notaEditing, setNotaEditing] = useState<Record<string, string>>({})

  const reservasQuery = useReservas(convocatoria?.id ?? '')
  const resultadosQuery = useResultados(convocatoria?.id ?? '')
  const saveResultadoMutation = useSaveResultado()
  const cerrarMutation = useCerrarConvocatoria()

  const handleSaveNota = async (alumnoId: string) => {
    if (!convocatoria) return
    const nota = notaEditing[alumnoId] ?? ''
    await saveResultadoMutation.mutateAsync({
      convId: convocatoria.id,
      payload: { alumno_id: alumnoId, nota_final: nota || undefined },
    })
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!convocatoria || !e.target.files?.[0]) return
    const file = e.target.files[0]
    // Read CSV and extract IDs (simplified: assume one UUID per line)
    const text = await file.text()
    const ids = text
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    await coloquiosService.importConvocados(convocatoria.id, ids)
  }

  const handleCerrar = async () => {
    if (!convocatoria) return
    if (!window.confirm('¿Cerrar esta convocatoria? No se aceptarán nuevas reservas.')) return
    await cerrarMutation.mutateAsync(convocatoria.id)
    onClose()
  }

  if (!open || !convocatoria) return null

  const TABS: { key: Tab; label: string }[] = [
    { key: 'convocados', label: 'Convocados' },
    { key: 'reservas', label: 'Reservas' },
    { key: 'resultados', label: 'Resultados' },
  ]

  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} role="presentation" />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Detalle de convocatoria"
        className="relative ml-auto flex h-full w-full max-w-xl flex-col bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Convocatoria</h2>
            <p className="text-xs text-slate-500">{convocatoria.instancia} — {convocatoria.estado}</p>
          </div>
          <div className="flex items-center gap-2">
            {convocatoria.estado === 'Abierta' && (
              <button
                type="button"
                onClick={handleCerrar}
                disabled={cerrarMutation.isPending}
                className="rounded border border-red-300 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
              >
                Cerrar convocatoria
              </button>
            )}
            <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="Cerrar">
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 px-6">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={[
                'px-4 py-2 text-sm font-medium transition-colors',
                tab === t.key
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-slate-500 hover:text-slate-700',
              ].join(' ')}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Convocados */}
          {tab === 'convocados' && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <label className="cursor-pointer rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50">
                  Importar desde archivo
                  <input type="file" accept=".csv,.txt" onChange={handleImport} className="hidden" />
                </label>
              </div>
              {convocados.length === 0 && (
                <p className="text-sm text-slate-500">Sin alumnos convocados todavía.</p>
              )}
              {convocados.map((c) => (
                <div key={c.id} className="flex items-center gap-2 rounded border border-slate-100 px-3 py-2">
                  <p className="text-xs font-mono text-slate-600">{c.alumno_id}</p>
                </div>
              ))}
            </div>
          )}

          {/* Reservas */}
          {tab === 'reservas' && (
            <div className="space-y-2">
              {reservasQuery.isLoading && <p className="text-sm text-slate-400">Cargando...</p>}
              {(reservasQuery.data ?? []).length === 0 && !reservasQuery.isLoading && (
                <p className="text-sm text-slate-500">Sin reservas todavía.</p>
              )}
              {(reservasQuery.data ?? []).map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded border border-slate-100 px-3 py-2">
                  <p className="text-xs font-mono text-slate-600">{r.alumno_id}</p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      r.estado === 'Activa' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {r.estado}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Resultados */}
          {tab === 'resultados' && (
            <div className="space-y-3">
              {resultadosQuery.isLoading && <p className="text-sm text-slate-400">Cargando...</p>}
              {(resultadosQuery.data ?? []).map((r) => (
                <div key={r.id} className="flex items-center gap-3 rounded border border-slate-100 px-3 py-2">
                  <p className="flex-1 text-xs font-mono text-slate-600">{r.alumno_id}</p>
                  <input
                    type="text"
                    placeholder="Nota"
                    defaultValue={r.nota_final ?? ''}
                    onChange={(e) =>
                      setNotaEditing((prev) => ({ ...prev, [r.alumno_id]: e.target.value }))
                    }
                    className="w-20 rounded border border-slate-300 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => void handleSaveNota(r.alumno_id)}
                    className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    Guardar
                  </button>
                </div>
              ))}
              {(resultadosQuery.data ?? []).length === 0 && !resultadosQuery.isLoading && (
                <p className="text-sm text-slate-500">Sin resultados registrados.</p>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  )
}
