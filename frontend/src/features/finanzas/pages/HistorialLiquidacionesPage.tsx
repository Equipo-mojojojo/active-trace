/**
 * HistorialLiquidacionesPage — Lista de períodos cerrados.
 *
 * Spec: frontend-liquidaciones §"Historial de liquidaciones cerradas"
 * Ruta: /finanzas/liquidaciones/historial
 * Permiso: liquidaciones:ver
 */
import { useState } from 'react'
import { useHistorialLiquidaciones } from '../hooks/useLiquidaciones'
import { useLiquidaciones } from '../hooks/useLiquidaciones'
import { SegmentoTab } from '../components/SegmentoTab'
import type { LiquidacionFilters } from '../types/finanzas.types'

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(amount)
}

export function HistorialLiquidacionesPage() {
  const [selectedPeriodo, setSelectedPeriodo] = useState<string | null>(null)
  const historialQuery = useHistorialLiquidaciones()

  const detailFilters: LiquidacionFilters = { periodo: selectedPeriodo ?? '' }
  const detalleQuery = useLiquidaciones(detailFilters)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Historial de Liquidaciones</h1>
        <p className="mt-1 text-sm text-slate-500">Períodos cerrados, de más reciente a más antiguo</p>
      </div>

      {historialQuery.isLoading && <p className="text-sm text-slate-500">Cargando historial...</p>}
      {historialQuery.isError && <p className="text-sm text-red-600">Error al cargar el historial.</p>}

      {historialQuery.data && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Período</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Cerrada en</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Sin factura</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Con factura</th>
                <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {historialQuery.data.map((item) => (
                <tr
                  key={item.periodo}
                  className={`cursor-pointer hover:bg-slate-50 ${selectedPeriodo === item.periodo ? 'bg-indigo-50' : ''}`}
                  onClick={() => setSelectedPeriodo(item.periodo === selectedPeriodo ? null : item.periodo)}
                >
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">{item.periodo}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                    {new Date(item.cerrada_en).toLocaleDateString('es-AR')}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                    {formatCurrency(item.total_sin_factura)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                    {formatCurrency(item.total_con_factura)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center text-sm">
                    <button
                      type="button"
                      className="text-indigo-600 hover:underline text-xs"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedPeriodo(item.periodo === selectedPeriodo ? null : item.periodo)
                      }}
                    >
                      {selectedPeriodo === item.periodo ? 'Ocultar detalle' : 'Ver detalle'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detalle del período seleccionado — solo lectura */}
      {selectedPeriodo && (
        <div className="rounded-xl border border-indigo-200 bg-white shadow-sm">
          <div className="border-b border-indigo-100 px-5 py-3">
            <h2 className="text-sm font-semibold text-indigo-700">
              Detalle período {selectedPeriodo} — Solo lectura
            </h2>
          </div>
          {detalleQuery.isLoading && (
            <p className="p-4 text-sm text-slate-500">Cargando detalle...</p>
          )}
          {detalleQuery.data && (
            <SegmentoTab docentes={[
              ...detalleQuery.data.general,
              ...detalleQuery.data.nexo,
              ...detalleQuery.data.facturantes,
            ]} />
          )}
        </div>
      )}
    </div>
  )
}
