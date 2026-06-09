/**
 * ModalAsignacionMasiva — modal para asignación masiva de docentes.
 *
 * Campos: docentes (IDs separados por coma), rol, comisiones, vigencia.
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAsignacionMasiva } from '../hooks/useEquipos'

const ROLES = ['TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO']

const schema = z.object({
  usuarios_raw: z.string().min(1, 'Ingresá al menos un UUID de docente'),
  rol: z.string().min(1, 'El rol es obligatorio'),
  comisiones: z.string().optional(),
  desde: z.string().min(1, 'La fecha de inicio es obligatoria'),
  hasta: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onClose: () => void
}

export function ModalAsignacionMasiva({ open, onClose }: Props) {
  const mutation = useAsignacionMasiva()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { usuarios_raw: '', rol: '', comisiones: '', desde: '', hasta: '' },
  })

  const onSubmit = async (data: FormData) => {
    const usuarios = data.usuarios_raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)

    await mutation.mutateAsync({
      usuarios,
      rol: data.rol,
      comisiones: data.comisiones || undefined,
      desde: data.desde,
      hasta: data.hasta || undefined,
    })
    reset()
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        role="presentation"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Asignación masiva"
        className="relative w-full max-w-lg rounded-xl bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Asignación masiva</h2>
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
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5 px-6 py-6">
          {/* Docentes */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              UUIDs de docentes (separados por coma) <span className="text-red-500">*</span>
            </label>
            <textarea
              {...register('usuarios_raw')}
              rows={3}
              placeholder="uuid-1, uuid-2, uuid-3"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.usuarios_raw && (
              <p className="mt-1 text-xs text-red-600">{errors.usuarios_raw.message}</p>
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
            <label className="mb-1 block text-sm font-medium text-slate-700">Comisiones</label>
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
                Desde <span className="text-red-500">*</span>
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
              <label className="mb-1 block text-sm font-medium text-slate-700">Hasta</label>
              <input
                type="date"
                {...register('hasta')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {mutation.isError && (
            <p className="text-xs text-red-600">Error al realizar la asignación masiva.</p>
          )}

          {/* Footer */}
          <div className="flex gap-3 border-t border-slate-100 pt-4">
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
              {isSubmitting ? 'Procesando...' : 'Confirmar asignación'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
