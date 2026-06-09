/**
 * ColoquiosPage — gestión de convocatorias de coloquio.
 *
 * Layout (from Stitch screen e3031247af39418b8a8788b1323af8f2):
 *  - Header + botón "Nueva convocatoria"
 *  - Lista de ConvocatoriaCard
 *  - DrawerConvocatoria
 *  - Modal "Nueva convocatoria"
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useColoquios, useCreateConvocatoria } from '../hooks/useColoquios'
import { coloquiosService } from '../services/coloquiosService'
import { ConvocatoriaCard } from '../components/ConvocatoriaCard'
import { DrawerConvocatoria } from '../components/DrawerConvocatoria'
import type { Convocatoria, Convocado, TipoEvaluacion } from '../types/coloquios.types'

const INSTANCIAS = ['1ra', '2da', 'Final', 'Recuperatorio']
const TIPOS: TipoEvaluacion[] = ['Parcial', 'TP', 'Coloquio', 'Recuperatorio']

const nuevaConvSchema = z.object({
  materia_id: z.string().min(1, 'La materia es obligatoria'),
  cohorte_id: z.string().min(1, 'La cohorte es obligatoria'),
  tipo: z.enum(['Parcial', 'TP', 'Coloquio', 'Recuperatorio'] as const),
  instancia: z.string().min(1, 'La instancia es obligatoria'),
  dias_disponibles: z.coerce.number().min(1),
  turno_fecha: z.string().min(1, 'La fecha del turno es obligatoria'),
  turno_hora: z.string().min(1, 'La hora del turno es obligatoria'),
  cupo: z.coerce.number().min(1, 'El cupo debe ser mayor a 0'),
})

type NuevaConvForm = z.infer<typeof nuevaConvSchema>

export function ColoquiosPage() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedConv, setSelectedConv] = useState<Convocatoria | null>(null)
  const [convocados, setConvocados] = useState<Convocado[]>([])
  const [modalOpen, setModalOpen] = useState(false)

  const coloquiosQuery = useColoquios()
  const createMutation = useCreateConvocatoria()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<NuevaConvForm>({
    resolver: zodResolver(nuevaConvSchema),
    defaultValues: {
      materia_id: '',
      cohorte_id: '',
      tipo: 'Coloquio',
      instancia: '1ra',
      dias_disponibles: 7,
      turno_fecha: '',
      turno_hora: '',
      cupo: 10,
    },
  })

  const handleVerDetalle = async (conv: Convocatoria) => {
    setSelectedConv(conv)
    // Load convocados
    const data = await coloquiosService.getColoquios() // just triggers refetch
    setConvocados([]) // will be loaded inside DrawerConvocatoria
    setDrawerOpen(true)
  }

  const onSubmit = async (data: NuevaConvForm) => {
    await createMutation.mutateAsync({
      materia_id: data.materia_id,
      cohorte_id: data.cohorte_id,
      tipo: data.tipo,
      instancia: data.instancia,
      dias_disponibles: data.dias_disponibles,
      turnos: [{ fecha: data.turno_fecha, hora: data.turno_hora, max_cupo: data.cupo }],
    })
    reset()
    setModalOpen(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Coloquios</h1>
          <p className="mt-1 text-sm text-slate-500">Gestión de convocatorias de evaluación</p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nueva convocatoria
        </button>
      </div>

      {/* Lista */}
      {coloquiosQuery.isLoading && (
        <p className="text-sm text-slate-500">Cargando convocatorias...</p>
      )}
      {coloquiosQuery.isError && (
        <p className="text-sm text-red-600">Error al cargar las convocatorias.</p>
      )}
      {!coloquiosQuery.isLoading && (coloquiosQuery.data ?? []).length === 0 && (
        <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm text-slate-500">No hay convocatorias. Creá la primera.</p>
        </div>
      )}
      <div className="space-y-4">
        {(coloquiosQuery.data ?? []).map((conv) => (
          <ConvocatoriaCard key={conv.id} convocatoria={conv} onVerDetalle={handleVerDetalle} />
        ))}
      </div>

      {/* Drawer */}
      <DrawerConvocatoria
        convocatoria={selectedConv}
        convocados={convocados}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false)
          setSelectedConv(null)
        }}
      />

      {/* Modal nueva convocatoria */}
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
            aria-label="Nueva convocatoria"
            className="relative w-full max-w-lg rounded-xl bg-white shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h2 className="text-base font-semibold text-slate-900">Nueva convocatoria</h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
                aria-label="Cerrar"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 px-6 py-6">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Materia ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    {...register('materia_id')}
                    placeholder="UUID"
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  {errors.materia_id && (
                    <p className="mt-1 text-xs text-red-600">{errors.materia_id.message}</p>
                  )}
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Cohorte ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    {...register('cohorte_id')}
                    placeholder="UUID"
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  {errors.cohorte_id && (
                    <p className="mt-1 text-xs text-red-600">{errors.cohorte_id.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Tipo</label>
                  <select
                    {...register('tipo')}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {TIPOS.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">Instancia</label>
                  <select
                    {...register('instancia')}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {INSTANCIAS.map((i) => (
                      <option key={i} value={i}>{i}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Fecha turno <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('turno_fecha')}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  {errors.turno_fecha && (
                    <p className="mt-1 text-xs text-red-600">{errors.turno_fecha.message}</p>
                  )}
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Hora <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="time"
                    {...register('turno_hora')}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Cupo <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    min={1}
                    {...register('cupo')}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  {errors.cupo && (
                    <p className="mt-1 text-xs text-red-600">{errors.cupo.message}</p>
                  )}
                </div>
              </div>

              {createMutation.isError && (
                <p className="text-xs text-red-600">Error al crear la convocatoria.</p>
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
                  {isSubmitting ? 'Creando...' : 'Crear convocatoria'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
