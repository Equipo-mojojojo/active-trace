/**
 * DrawerPublicarAviso — panel lateral para publicar un aviso institucional.
 *
 * Formulario (from Stitch screen 555dba071889406ca47524eed207a5df):
 *  - Título (texto, obligatorio)
 *  - Cuerpo (textarea)
 *  - Severidad (radio: Info / Advertencia / Crítico)
 *  - Alcance (dropdown: Global / PorMateria / PorCohorte / PorRol)
 *  - Campo condicional según alcance (materia_id / cohorte_id / rol_destino)
 *  - Vigencia desde / hasta (date-pickers)
 *  - Toggle "Requiere confirmación de lectura"
 */
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateAviso } from '../hooks/useAvisos'
import type { AlcanceAviso, SeveridadAviso } from '../types/coordinacion.types'

const schema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio'),
  cuerpo: z.string().min(1, 'El cuerpo es obligatorio'),
  severidad: z.enum(['Info', 'Advertencia', 'Crítico'] as const),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol'] as const),
  materia_id: z.string().optional(),
  cohorte_id: z.string().optional(),
  rol_destino: z.string().optional(),
  inicio_en: z.string().min(1, 'La fecha de inicio es obligatoria'),
  fin_en: z.string().optional(),
  requiere_ack: z.boolean(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onClose: () => void
}

const SEVERIDADES: SeveridadAviso[] = ['Info', 'Advertencia', 'Crítico']
const ALCANCES: { value: AlcanceAviso; label: string }[] = [
  { value: 'Global', label: 'Global' },
  { value: 'PorMateria', label: 'Por materia' },
  { value: 'PorCohorte', label: 'Por cohorte' },
  { value: 'PorRol', label: 'Por rol' },
]

export function DrawerPublicarAviso({ open, onClose }: Props) {
  const createMutation = useCreateAviso()

  const {
    register,
    handleSubmit,
    watch,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      titulo: '',
      cuerpo: '',
      severidad: 'Info',
      alcance: 'Global',
      requiere_ack: false,
      inicio_en: '',
      fin_en: '',
    },
  })

  const alcanceValue = watch('alcance')

  const onSubmit = async (data: FormData) => {
    await createMutation.mutateAsync({
      titulo: data.titulo,
      cuerpo: data.cuerpo,
      severidad: data.severidad,
      alcance: data.alcance,
      materia_id: data.materia_id || undefined,
      cohorte_id: data.cohorte_id || undefined,
      rol_destino: data.rol_destino || undefined,
      inicio_en: new Date(data.inicio_en).toISOString(),
      fin_en: data.fin_en ? new Date(data.fin_en).toISOString() : undefined,
      requiere_ack: data.requiere_ack,
      activo: true,
    })
    reset()
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 flex">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} role="presentation" />

      {/* Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Publicar aviso"
        className="relative ml-auto flex h-full w-full max-w-md flex-col bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Publicar aviso</h2>
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
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-1 flex-col gap-5 overflow-y-auto px-6 py-6"
        >
          {/* Título */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Título <span className="text-red-500">*</span>
            </label>
            <input
              {...register('titulo')}
              placeholder="Título del aviso"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.titulo && (
              <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>
            )}
          </div>

          {/* Cuerpo */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Cuerpo</label>
            <textarea
              {...register('cuerpo')}
              rows={4}
              placeholder="Contenido del aviso..."
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.cuerpo && (
              <p className="mt-1 text-xs text-red-600">{errors.cuerpo.message}</p>
            )}
          </div>

          {/* Severidad */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Severidad</label>
            <div className="flex gap-4">
              {SEVERIDADES.map((sev) => (
                <label key={sev} className="flex items-center gap-1.5 text-sm text-slate-700">
                  <input type="radio" value={sev} {...register('severidad')} />
                  {sev}
                </label>
              ))}
            </div>
          </div>

          {/* Alcance */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Alcance</label>
            <select
              {...register('alcance')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ALCANCES.map((a) => (
                <option key={a.value} value={a.value}>{a.label}</option>
              ))}
            </select>
          </div>

          {/* Campo condicional */}
          {alcanceValue === 'PorMateria' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                ID de materia
              </label>
              <input
                {...register('materia_id')}
                placeholder="UUID de la materia"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}
          {alcanceValue === 'PorCohorte' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                ID de cohorte
              </label>
              <input
                {...register('cohorte_id')}
                placeholder="UUID de la cohorte"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}
          {alcanceValue === 'PorRol' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Rol destino</label>
              <input
                {...register('rol_destino')}
                placeholder="Ej: PROFESOR"
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {/* Vigencia */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Vigencia desde <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                {...register('inicio_en')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {errors.inicio_en && (
                <p className="mt-1 text-xs text-red-600">{errors.inicio_en.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Vigencia hasta</label>
              <input
                type="datetime-local"
                {...register('fin_en')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Toggle ack */}
          <div className="flex items-center gap-3">
            <Controller
              control={control}
              name="requiere_ack"
              render={({ field }) => (
                <input
                  type="checkbox"
                  id="requiere_ack"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
              )}
            />
            <label htmlFor="requiere_ack" className="text-sm text-slate-700">
              Requiere confirmación de lectura
            </label>
          </div>

          {createMutation.isError && (
            <p className="text-xs text-red-600">Error al publicar el aviso. Intentá de nuevo.</p>
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
              {isSubmitting ? 'Publicando...' : 'Publicar'}
            </button>
          </div>
        </form>
      </aside>
    </div>
  )
}
