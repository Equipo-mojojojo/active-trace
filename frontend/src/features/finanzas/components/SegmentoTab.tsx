import type { DocenteEnLiquidacion } from '../types/finanzas.types'
import { RolBadge } from './RolBadge'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 0,
  }).format(amount)
}

interface SegmentoTabProps {
  docentes: DocenteEnLiquidacion[]
  emptyMessage?: string
}

export function SegmentoTab({ docentes, emptyMessage = 'Sin docentes en este segmento' }: SegmentoTabProps) {
  if (docentes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500">
        <p className="text-sm">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Docente</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Rol</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Comisiones</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Salario Base</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Plus</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {docentes.map((d) => (
            <tr key={d.usuario_id} className="hover:bg-slate-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">{d.nombre}</td>
              <td className="whitespace-nowrap px-4 py-3">
                <RolBadge rol={d.rol} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{d.comisiones}</td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{formatCurrency(d.salario_base)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{formatCurrency(d.plus)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-semibold text-slate-900">{formatCurrency(d.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
