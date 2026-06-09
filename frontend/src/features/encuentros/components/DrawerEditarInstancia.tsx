/**
 * DrawerEditarInstancia — panel para editar una instancia de encuentro.
 *
 * Campos:
 *  - Estado (select: Programado / Realizado / Cancelado)
 *  - Meet URL
 *  - Video URL (grabación)
 *  - Comentario
 */
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useUpdateInstancia } from '../hooks/useEncuentros'
import type { InstanciaEncuentro, EstadoEncuentro } from '../types/encuentros.types'

const ESTADOS: EstadoEncuentro[] = ['Programado', 'Realizado', 'Cancelado']

const schema = z.object({
  estado: z.enum(['Programado', 'Realizado', 'Cancelado'] as const),
  meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
  video_url: z.string().url('URL inválida').optional().or(z.literal('')),
  comentario: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  instancia: InstanciaEncuentro | null
  open: boolean
  onClose: () => void
}

export function DrawerEditarInstancia({ instancia, open, onClose }: Props) {
  const updateMutation = useUpdateInstancia()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { estado: 'Programado', meet_url: '', video_url: '', comentario: '' },
  })

  useEffect(() => {
    if (instancia) {
      reset({
        estado: instancia.estado,
        meet_url: instancia.meet_url ?? '',
        video_url: instancia.video_url ?? '',
        comentario: instancia.comentario ?? '',
      })
    }
  }, [instancia, reset])

  const onSubmit = async (data: FormData) => {
    if (!instancia) return
    await updateMutation.mutateAsync({
      id: instancia.id,
      payload: {
        estado: data.estado,
        meet_url: data.meet_url || undefined,
        video_url: data.video_url || undefined,
        comentario: data.comentario || undefined,
      },
    })
    onClose()
  }

  if (!open || !instancia) return null

  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} role="presentation" />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Editar instancia"
        className="relative ml-auto flex h-full w-full max-w-md flex-col bg-white shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Editar instancia</h2>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="Cerrar">
            ✕
          </button>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-1 flex-col gap-5 overflow-y-auto px-6 py-6">
          {/* Info de la instancia */}
          <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-500">
            {instancia.titulo} — {instancia.fecha} {instancia.hora}
          </div>

          {/* Estado */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Estado</label>
            <select
              {...register('estado')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ESTADOS.map((e) => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          </div>

          {/* Meet URL */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Meet URL</label>
            <input
              {...register('meet_url')}
              type="url"
              placeholder="https://meet.google.com/..."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.meet_url && <p className="mt-1 text-xs text-red-600">{errors.meet_url.message}</p>}
          </div>

          {/* Video URL */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Video URL (grabación)</label>
            <input
              {...register('video_url')}
              type="url"
              placeholder="https://drive.google.com/..."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.video_url && <p className="mt-1 text-xs text-red-600">{errors.video_url.message}</p>}
          </div>

          {/* Comentario */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Comentario</label>
            <textarea
              {...register('comentario')}
              rows={3}
              placeholder="Notas sobre esta instancia..."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {updateMutation.isError && (
            <p className="text-xs text-red-600">Error al actualizar la instancia.</p>
          )}

          <div className="mt-auto flex gap-3 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </aside>
    </div>
  )
}
