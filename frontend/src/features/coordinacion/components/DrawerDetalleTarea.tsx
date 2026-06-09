/**
 * DrawerDetalleTarea — panel lateral de detalle de una tarea.
 *
 * Contenido (from Stitch screen 8d5c3c2e698c428ca2dead29ddbaea84):
 *  - Título / descripción
 *  - Select de estado (editable)
 *  - HiloComentarios
 */
import { useState } from 'react'
import { useUpdateEstadoTarea } from '../hooks/useTareas'
import { HiloComentarios } from './HiloComentarios'
import type { Tarea, EstadoTarea } from '../types/coordinacion.types'

const ESTADOS: EstadoTarea[] = ['Pendiente', 'En progreso', 'Resuelta', 'Cancelada']

interface Props {
  tarea: Tarea | null
  open: boolean
  onClose: () => void
}

export function DrawerDetalleTarea({ tarea, open, onClose }: Props) {
  const [estado, setEstado] = useState<EstadoTarea>(tarea?.estado ?? 'Pendiente')
  const updateMutation = useUpdateEstadoTarea()

  const handleSaveEstado = async () => {
    if (!tarea || estado === tarea.estado) return
    await updateMutation.mutateAsync({ id: tarea.id, estado })
  }

  if (!open || !tarea) return null

  return (
    <div className="fixed inset-0 z-40 flex">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} role="presentation" />

      {/* Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Detalle de tarea"
        className="relative ml-auto flex h-full w-full max-w-lg flex-col bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Detalle de tarea</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 flex-col gap-5 overflow-y-auto px-6 py-6">
          {/* Descripción */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Descripción
            </p>
            <p className="mt-1 text-sm text-slate-700">{tarea.descripcion}</p>
          </div>

          {/* Asignaciones */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Asignado a
              </p>
              <p className="mt-1 text-xs text-slate-600 font-mono">{tarea.asignado_a}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Asignado por
              </p>
              <p className="mt-1 text-xs text-slate-600 font-mono">{tarea.asignado_por}</p>
            </div>
          </div>

          {/* Estado */}
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-400">
              Estado
            </label>
            <div className="flex items-center gap-2">
              <select
                value={estado}
                onChange={(e) => setEstado(e.target.value as EstadoTarea)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {ESTADOS.map((e) => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
              {estado !== tarea.estado && (
                <button
                  type="button"
                  onClick={() => void handleSaveEstado()}
                  disabled={updateMutation.isPending}
                  className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {updateMutation.isPending ? 'Guardando...' : 'Guardar estado'}
                </button>
              )}
            </div>
            {updateMutation.isError && (
              <p className="mt-1 text-xs text-red-600">Error al actualizar el estado.</p>
            )}
          </div>

          {/* Hilo de comentarios */}
          <div className="border-t border-slate-100 pt-4">
            <HiloComentarios tareaId={tarea.id} />
          </div>
        </div>
      </aside>
    </div>
  )
}
