/**
 * TareasPage — gestión de tareas internas.
 *
 * Layout (from Stitch screen 8d5c3c2e698c428ca2dead29ddbaea84):
 *  - Header "Tareas" + botón "Nueva tarea"
 *  - Tabs: Mis tareas / Asignadas por mí / Todas (query param ?tab=)
 *  - Tabla de TareaRow
 *  - DrawerDetalleTarea
 *  - Modal "Nueva tarea"
 */
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTareas, useCreateTarea } from '../hooks/useTareas'
import { TareaRow } from '../components/TareaRow'
import { DrawerDetalleTarea } from '../components/DrawerDetalleTarea'
import type { Tarea } from '../types/coordinacion.types'
import type { TareaTab } from '../services/tareasService'

const TABS: { key: TareaTab; label: string }[] = [
  { key: 'mias', label: 'Mis tareas' },
  { key: 'asignadas', label: 'Asignadas por mí' },
  { key: 'todas', label: 'Todas' },
]

const nuevaTareaSchema = z.object({
  descripcion: z.string().min(1, 'El título es obligatorio'),
  asignado_a: z.string().min(1, 'Debés asignar la tarea a alguien'),
})

type NuevaTareaForm = z.infer<typeof nuevaTareaSchema>

export function TareasPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = (searchParams.get('tab') as TareaTab) || 'mias'
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedTarea, setSelectedTarea] = useState<Tarea | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const tareasQuery = useTareas(tab)
  const createMutation = useCreateTarea()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<NuevaTareaForm>({
    resolver: zodResolver(nuevaTareaSchema),
    defaultValues: { descripcion: '', asignado_a: '' },
  })

  const handleTabChange = (newTab: TareaTab) => {
    setSearchParams({ tab: newTab })
  }

  const handleVerDetalle = (tarea: Tarea) => {
    setSelectedTarea(tarea)
    setDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setDrawerOpen(false)
    setSelectedTarea(null)
  }

  const onSubmitNuevaTarea = async (data: NuevaTareaForm) => {
    await createMutation.mutateAsync({
      descripcion: data.descripcion,
      asignado_a: data.asignado_a,
    })
    reset()
    setModalOpen(false)
  }

  const tareas = tareasQuery.data ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Tareas</h1>
          <p className="mt-1 text-sm text-slate-500">Gestión de tareas del equipo de coordinación</p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nueva tarea
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => handleTabChange(t.key)}
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

      {/* Tabla */}
      {tareasQuery.isLoading && <p className="text-sm text-slate-500">Cargando tareas...</p>}
      {tareasQuery.isError && <p className="text-sm text-red-600">Error al cargar las tareas.</p>}
      {!tareasQuery.isLoading && tareas.length === 0 && (
        <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm text-slate-500">No tenés tareas en este momento.</p>
        </div>
      )}
      {!tareasQuery.isLoading && tareas.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-100">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                  Descripción
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                  Asignado a
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                  Asignado por
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">
                  Estado
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {tareas.map((tarea) => (
                <TareaRow key={tarea.id} tarea={tarea} onVerDetalle={handleVerDetalle} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Drawer detalle */}
      <DrawerDetalleTarea tarea={selectedTarea} open={drawerOpen} onClose={handleCloseDrawer} />

      {/* Modal nueva tarea */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setModalOpen(false)}
            role="presentation"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Nueva tarea"
            className="relative w-full max-w-md rounded-xl bg-white shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h2 className="text-base font-semibold text-slate-900">Nueva tarea</h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
                aria-label="Cerrar"
              >
                ✕
              </button>
            </div>
            <form
              onSubmit={handleSubmit(onSubmitNuevaTarea)}
              className="flex flex-col gap-5 px-6 py-6"
            >
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Descripción <span className="text-red-500">*</span>
                </label>
                <textarea
                  {...register('descripcion')}
                  rows={3}
                  placeholder="Descripción de la tarea"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {errors.descripcion && (
                  <p className="mt-1 text-xs text-red-600">{errors.descripcion.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Asignar a (UUID) <span className="text-red-500">*</span>
                </label>
                <input
                  {...register('asignado_a')}
                  placeholder="UUID del usuario"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {errors.asignado_a && (
                  <p className="mt-1 text-xs text-red-600">{errors.asignado_a.message}</p>
                )}
              </div>
              {createMutation.isError && (
                <p className="text-xs text-red-600">Error al crear la tarea.</p>
              )}
              <div className="flex gap-3 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Creando...' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
