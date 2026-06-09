/**
 * DrawerAsignacion — panel lateral para crear o editar una asignación docente.
 *
 * Formulario (from Stitch screen 9368f556d4584ff4a0cae673ca93eb4e):
 *  - Docente (usuario_id — select/input)
 *  - Rol (select)
 *  - Comisiones (texto)
 *  - Vigencia desde / hasta (date inputs)
 *  - Botón Guardar
 */
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateAsignacion, useUpdateAsignacion } from '../hooks/useEquipos'
import type { Asignacion } from '../types/coordinacion.types'

const ROLES = ['TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO']

const schema = z.object({
  usuario_id: z.string().min(1, 'El docente es obligatorio'),
  rol: z.string().min(1, 'El rol es obligatorio'),
  comisiones: z.string().optional(),
  desde: z.string().min(1, 'La fecha de inicio es obligatoria'),
  hasta: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  asignacion?: Asignacion | null
  open: boolean
  onClose: () => void
}

export function DrawerAsignacion({ asignacion, open, onClose }: Props) {
  const createMutation = useCreateAsignacion()
  const updateMutation = useUpdateAsignacion()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      usuario_id: '',
      rol: '',
      comisiones: '',
      desde: '',
      hasta: '',
    },
  })

  useEffect(() => {
    if (asignacion) {
      reset({
        usuario_id: asignacion.usuario_id,
        rol: asignacion.rol,
        comisiones: asignacion.comisiones ?? '',
        desde: asignacion.desde,
        hasta: asignacion.hasta ?? '',
      })
    } else {
      reset({ usuario_id: '', rol: '', comisiones: '', desde: '', hasta: '' })
    }
  }, [asignacion, reset])

  const onSubmit = async (data: FormData) => {
    const payload = {
      usuario_id: data.usuario_id,
      rol: data.rol,
      comisiones: data.comisiones || undefined,
      desde: data.desde,
      hasta: data.hasta || undefined,
    }

    if (asignacion) {
      await updateMutation.mutateAsync({ id: asignacion.id, payload })
    } else {
      await createMutation.mutateAsync(payload)
    }
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 flex">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        role="presentation"
      />

      {/* Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={asignacion ? 'Editar asignación' : 'Nueva asignación'}
        className="relative ml-auto flex h-full w-full max-w-md flex-col bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">
            {asignacion ? 'Editar asignación' : 'Nueva asignación'}
          </h2>
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
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-1 flex-col gap-5 overflow-y-auto px-6 py-6">
          {/* Usuario ID */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              ID del docente <span className="text-red-500">*</span>
            </label>
            <input
              {...register('usuario_id')}
              placeholder="UUID del docente"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.usuario_id && (
              <p className="mt-1 text-xs text-red-600">{errors.usuario_id.message}</p>
            )}
          </div>

          {/* Rol */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Rol <span className="text-red-500">*</span>
            </label>
            <select
              {...register('rol')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Seleccionar rol</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            {errors.rol && (
              <p className="mt-1 text-xs text-red-600">{errors.rol.message}</p>
            )}
          </div>

          {/* Comisiones */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Comisiones
            </label>
            <input
              {...register('comisiones')}
              placeholder="Ej: A, B"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Vigencia */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Vigencia desde <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                {...register('desde')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {errors.desde && (
                <p className="mt-1 text-xs text-red-600">{errors.desde.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Vigencia hasta
              </label>
              <input
                type="date"
                {...register('hasta')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Error general */}
          {(createMutation.isError || updateMutation.isError) && (
            <p className="text-xs text-red-600">
              Error al guardar la asignación. Intentá de nuevo.
            </p>
          )}

          {/* Footer */}
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
