/**
 * ModalNuevoEncuentro — modal para crear un nuevo encuentro (recurrente o único).
 *
 * Campos:
 *  - Título (texto)
 *  - Tipo (Recurrente / Único)
 *  - Asignación ID (UUID)
 *  - Materia ID (UUID)
 *  - Día de la semana + hora (para recurrente)
 *  - Fecha específica (para único)
 *  - Meet URL (opcional)
 *  - Cantidad de semanas (para recurrente)
 *  - Vigencia desde / hasta
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateEncuentro } from '../hooks/useEncuentros'
import type { DiaSemana } from '../types/encuentros.types'

const DIAS: DiaSemana[] = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const schema = z
  .object({
    titulo: z.string().min(1, 'El título es obligatorio'),
    tipo: z.enum(['recurrente', 'unico']),
    asignacion_id: z.string().min(1, 'La asignación es obligatoria'),
    materia_id: z.string().min(1, 'La materia es obligatoria'),
    dia_semana: z.string().optional(),
    hora: z.string().min(1, 'La hora es obligatoria'),
    fecha_unica: z.string().optional(),
    meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
    cant_semanas: z.coerce.number().min(1).optional(),
    vig_desde: z.string().min(1, 'La vigencia desde es obligatoria'),
    vig_hasta: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.tipo === 'recurrente' && !data.dia_semana) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'El día de la semana es obligatorio para encuentros recurrentes',
        path: ['dia_semana'],
      })
    }
    if (data.tipo === 'unico' && !data.fecha_unica) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'La fecha específica es obligatoria para encuentros únicos',
        path: ['fecha_unica'],
      })
    }
  })

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onClose: () => void
}

export function ModalNuevoEncuentro({ open, onClose }: Props) {
  const createMutation = useCreateEncuentro()

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      titulo: '',
      tipo: 'recurrente',
      asignacion_id: '',
      materia_id: '',
      dia_semana: 'Lunes',
      hora: '',
      meet_url: '',
      cant_semanas: 10,
      vig_desde: '',
      vig_hasta: '',
    },
  })

  const tipo = watch('tipo')

  const onSubmit = async (data: FormData) => {
    await createMutation.mutateAsync({
      titulo: data.titulo,
      asignacion_id: data.asignacion_id,
      materia_id: data.materia_id,
      dia_semana: (data.dia_semana as DiaSemana) ?? 'Lunes',
      hora: data.hora,
      fecha_inicio: data.vig_desde,
      fecha_unica: data.tipo === 'unico' ? data.fecha_unica : undefined,
      meet_url: data.meet_url || undefined,
      cant_semanas: data.tipo === 'recurrente' ? data.cant_semanas : 0,
      vig_desde: data.vig_desde,
      vig_hasta: data.vig_hasta || undefined,
    })
    reset()
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} role="presentation" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Nuevo encuentro"
        className="relative w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl max-h-screen"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Nuevo encuentro</h2>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="Cerrar">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 px-6 py-6">
          {/* Título */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Título <span className="text-red-500">*</span>
            </label>
            <input
              {...register('titulo')}
              placeholder="Ej: Clase de Matemática I"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.titulo && <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>}
          </div>

          {/* Tipo */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Tipo</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-sm">
                <input type="radio" value="recurrente" {...register('tipo')} />
                Recurrente
              </label>
              <label className="flex items-center gap-1.5 text-sm">
                <input type="radio" value="unico" {...register('tipo')} />
                Único
              </label>
            </div>
          </div>

          {/* IDs */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Asignación ID <span className="text-red-500">*</span>
              </label>
              <input
                {...register('asignacion_id')}
                placeholder="UUID"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {errors.asignacion_id && (
                <p className="mt-1 text-xs text-red-600">{errors.asignacion_id.message}</p>
              )}
            </div>
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
          </div>

          {/* Recurrente fields */}
          {tipo === 'recurrente' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Día de la semana
                </label>
                <select
                  {...register('dia_semana')}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {DIAS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                {errors.dia_semana && (
                  <p className="mt-1 text-xs text-red-600">{errors.dia_semana.message}</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Cantidad de semanas
                </label>
                <input
                  type="number"
                  {...register('cant_semanas')}
                  min={1}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Único field */}
          {tipo === 'unico' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Fecha específica <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                {...register('fecha_unica')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {errors.fecha_unica && (
                <p className="mt-1 text-xs text-red-600">{errors.fecha_unica.message}</p>
              )}
            </div>
          )}

          {/* Hora */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Hora <span className="text-red-500">*</span>
            </label>
            <input
              type="time"
              {...register('hora')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.hora && <p className="mt-1 text-xs text-red-600">{errors.hora.message}</p>}
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
            {errors.meet_url && (
              <p className="mt-1 text-xs text-red-600">{errors.meet_url.message}</p>
            )}
          </div>

          {/* Vigencia */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Vigencia desde <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                {...register('vig_desde')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {errors.vig_desde && (
                <p className="mt-1 text-xs text-red-600">{errors.vig_desde.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Vigencia hasta</label>
              <input
                type="date"
                {...register('vig_hasta')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {createMutation.isError && (
            <p className="text-xs text-red-600">Error al crear el encuentro.</p>
          )}

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
              {isSubmitting ? 'Creando...' : 'Crear encuentro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
