/**
 * FacturasPage — Gestión de facturas de docentes.
 *
 * Layout (Stitch: Gestión de Facturas de Docentes):
 *  - Header con título + botón "Nueva factura" (requiere facturas:gestionar)
 *  - Filtros (docente, estado, rango fechas, búsqueda)
 *  - Tabla de comprobantes con badges de estado
 *  - Formulario nueva factura (modal inline)
 *  - Adjuntar archivo + cambiar estado por fila
 *
 * Spec: frontend-facturas
 */
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { usePermission } from '@/shared/hooks/usePermission'
import { useFacturas, useCrearFactura, useCambiarEstadoFactura, useAdjuntarArchivo } from '../hooks/useFacturas'
import type { FacturaFilters, EstadoFactura } from '../types/finanzas.types'
import axios from 'axios'

const nuevaFacturaSchema = z.object({
  usuario_id: z.string().min(1, 'Requerido'),
  periodo: z.string().min(1, 'Requerido'),
  monto: z.coerce.number().positive('Debe ser positivo'),
  detalle: z.string().min(1, 'Requerido'),
  fecha_carga: z.string().min(1, 'Requerido'),
})
type NuevaFacturaForm = z.infer<typeof nuevaFacturaSchema>

const ESTADO_BADGE: Record<EstadoFactura, string> = {
  pendiente: 'bg-amber-100 text-amber-800',
  abonada: 'bg-green-100 text-green-800',
}

export function FacturasPage() {
  const { hasPermission } = usePermission()
  const canGestionar = hasPermission('facturas:gestionar')

  const [filters, setFilters] = useState<FacturaFilters>({})
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const facturasQuery = useFacturas(filters)
  const crearMutation = useCrearFactura()
  const cambiarEstadoMutation = useCambiarEstadoFactura()
  const adjuntarMutation = useAdjuntarArchivo()

  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({})

  const { register, handleSubmit, reset, formState: { errors } } = useForm<NuevaFacturaForm>({
    resolver: zodResolver(nuevaFacturaSchema),
  })

  const onSubmitNuevaFactura = async (values: NuevaFacturaForm) => {
    setFormError(null)
    try {
      await crearMutation.mutateAsync(values)
      setFormOpen(false)
      reset()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        setFormError('El docente seleccionado no es facturante.')
      } else {
        setFormError('Error al crear la factura.')
      }
    }
  }

  const handleCambiarEstado = async (id: string, estadoActual: EstadoFactura) => {
    const nuevoEstado: EstadoFactura = estadoActual === 'pendiente' ? 'abonada' : 'pendiente'
    await cambiarEstadoMutation.mutateAsync({ id, estado: nuevoEstado })
  }

  const handleAdjuntar = async (id: string, file: File) => {
    await adjuntarMutation.mutateAsync({ id, file })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Facturas de Docentes</h1>
          <p className="mt-1 text-sm text-slate-500">Comprobantes de docentes facturantes</p>
        </div>
        {canGestionar && (
          <button
            type="button"
            onClick={() => setFormOpen(true)}
            aria-label="Nueva factura"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Nueva factura
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <input
          type="text"
          placeholder="Buscar..."
          value={filters.q ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value || undefined }))}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select
          value={filters.estado ?? ''}
          onChange={(e) =>
            setFilters((f) => ({ ...f, estado: (e.target.value as EstadoFactura) || undefined }))
          }
          aria-label="Filtrar por estado"
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="abonada">Abonada</option>
        </select>
        <input
          type="date"
          value={filters.fecha_desde ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined }))}
          aria-label="Desde"
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <input
          type="date"
          value={filters.fecha_hasta ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined }))}
          aria-label="Hasta"
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Formulario nueva factura */}
      {formOpen && (
        <div className="rounded-xl border border-indigo-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-slate-900">Nueva factura</h2>
          {formError && (
            <p className="mb-3 text-sm text-red-600" role="alert">{formError}</p>
          )}
          <form onSubmit={handleSubmit(onSubmitNuevaFactura)} className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">ID Docente *</label>
              <input {...register('usuario_id')} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
              {errors.usuario_id && <p className="mt-0.5 text-xs text-red-600">{errors.usuario_id.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Período *</label>
              <input type="month" {...register('periodo')} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
              {errors.periodo && <p className="mt-0.5 text-xs text-red-600">{errors.periodo.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Monto *</label>
              <input type="number" {...register('monto')} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
              {errors.monto && <p className="mt-0.5 text-xs text-red-600">{errors.monto.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Fecha de carga *</label>
              <input type="date" {...register('fecha_carga')} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
              {errors.fecha_carga && <p className="mt-0.5 text-xs text-red-600">{errors.fecha_carga.message}</p>}
            </div>
            <div className="col-span-2">
              <label className="mb-1 block text-xs font-medium text-slate-600">Detalle *</label>
              <input {...register('detalle')} className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
              {errors.detalle && <p className="mt-0.5 text-xs text-red-600">{errors.detalle.message}</p>}
            </div>
            <div className="col-span-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setFormOpen(false); reset(); setFormError(null) }}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearMutation.isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {crearMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tabla */}
      {facturasQuery.isLoading && <p className="text-sm text-slate-500">Cargando facturas...</p>}
      {facturasQuery.isError && <p className="text-sm text-red-600">Error al cargar las facturas.</p>}

      {facturasQuery.data && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Docente</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Período</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Detalle</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Monto</th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Adjunto</th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Estado</th>
                {canGestionar && (
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {facturasQuery.data.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                    {new Date(f.fecha_carga).toLocaleDateString('es-AR')}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">{f.nombre_docente}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{f.periodo}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{f.detalle}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                    {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(f.monto)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center text-sm">
                    {f.archivo_path ? (
                      <span className="text-green-600" title="Archivo adjunto">✓</span>
                    ) : canGestionar ? (
                      <>
                        <input
                          type="file"
                          className="hidden"
                          ref={(el) => { fileInputRefs.current[f.id] = el }}
                          onChange={(e) => {
                            const file = e.target.files?.[0]
                            if (file) handleAdjuntar(f.id, file)
                          }}
                          aria-label={`Adjuntar archivo a factura ${f.id}`}
                        />
                        <button
                          type="button"
                          onClick={() => fileInputRefs.current[f.id]?.click()}
                          className="text-xs text-indigo-600 hover:underline"
                        >
                          Adjuntar
                        </button>
                      </>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${ESTADO_BADGE[f.estado]}`}>
                      {f.estado === 'pendiente' ? 'Pendiente' : 'Abonada'}
                    </span>
                  </td>
                  {canGestionar && (
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <button
                        type="button"
                        onClick={() => handleCambiarEstado(f.id, f.estado)}
                        aria-label={`Cambiar estado de factura ${f.id}`}
                        className="text-indigo-600 hover:underline text-xs"
                      >
                        Cambiar estado
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {facturasQuery.data.length === 0 && (
                <tr>
                  <td colSpan={canGestionar ? 8 : 7} className="py-8 text-center text-sm text-slate-500">
                    Sin comprobantes para los filtros seleccionados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
