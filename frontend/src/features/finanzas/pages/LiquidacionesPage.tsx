/**
 * LiquidacionesPage — Panel de liquidaciones segmentado.
 *
 * Layout (Stitch: Panel de Liquidaciones - Finanzas):
 *  - Header con título, filtros (cohorte, mes, docente) y botones Cerrar/Exportar
 *  - KPI cards (Total sin factura / Total con factura)
 *  - 3 tabs: General / NEXO / Facturas
 *  - Tabla de docentes por segmento
 *
 * Spec: frontend-liquidaciones
 * D2: Una sola request, tabs cambian el segmento sin re-fetch.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePermission } from '@/shared/hooks/usePermission'
import { useLiquidaciones, useCerrarLiquidacion } from '../hooks/useLiquidaciones'
import { liquidacionesService } from '../services/liquidacionesService'
import { SegmentoTab } from '../components/SegmentoTab'
import { ConfirmModal } from '../components/ConfirmModal'
import type { LiquidacionFilters } from '../types/finanzas.types'
import axios from 'axios'

type TabId = 'general' | 'nexo' | 'facturantes'

const TABS: { id: TabId; label: string }[] = [
  { id: 'general', label: 'General' },
  { id: 'nexo', label: 'NEXO' },
  { id: 'facturantes', label: 'Facturas' },
]

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(amount)
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function LiquidacionesPage() {
  const { hasPermission } = usePermission()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<TabId>('general')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [cerrarError, setCerrarError] = useState<string | null>(null)
  const [filters, setFilters] = useState<LiquidacionFilters>({
    periodo: new Date().toISOString().slice(0, 7), // YYYY-MM default
  })

  const liquidacionQuery = useLiquidaciones(filters)
  const cerrarMutation = useCerrarLiquidacion()
  const canCerrar = hasPermission('liquidaciones:cerrar')

  const data = liquidacionQuery.data

  const handleCerrar = async () => {
    setCerrarError(null)
    try {
      await cerrarMutation.mutateAsync(filters.periodo)
      setConfirmOpen(false)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setCerrarError('La liquidación ya está cerrada.')
      } else {
        setCerrarError('Error al cerrar la liquidación.')
      }
      setConfirmOpen(false)
    }
  }

  const handleExportar = async () => {
    const blob = await liquidacionesService.exportarLiquidacion(filters)
    downloadBlob(blob, `liquidacion-${filters.periodo}.xlsx`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Liquidaciones</h1>
          <p className="mt-1 text-sm text-slate-500">Panel de liquidaciones docentes por período</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleExportar}
            aria-label="Exportar liquidación"
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Exportar
          </button>
          {canCerrar && !data?.cerrada && (
            <button
              type="button"
              onClick={() => setConfirmOpen(true)}
              aria-label="Cerrar liquidación"
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Cerrar liquidación
            </button>
          )}
          <button
            type="button"
            onClick={() => navigate('/finanzas/liquidaciones/historial')}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Ver historial
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label htmlFor="periodo" className="mb-1 block text-xs font-medium text-slate-600">
            Período (mes)
          </label>
          <input
            id="periodo"
            type="month"
            value={filters.periodo}
            onChange={(e) => setFilters((f) => ({ ...f, periodo: e.target.value }))}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label htmlFor="usuario_id" className="mb-1 block text-xs font-medium text-slate-600">
            Docente (ID, opcional)
          </label>
          <input
            id="usuario_id"
            type="text"
            placeholder="ID del docente"
            value={filters.usuario_id ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, usuario_id: e.target.value || undefined }))
            }
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Error messages */}
      {cerrarError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">
          {cerrarError}
        </div>
      )}
      {data?.cerrada && (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-700" role="status">
          Esta liquidación está cerrada (solo lectura).
        </div>
      )}

      {/* Loading / Error */}
      {liquidacionQuery.isLoading && (
        <p className="text-sm text-slate-500">Cargando liquidación...</p>
      )}
      {liquidacionQuery.isError && (
        <p className="text-sm text-red-600">Error al cargar la liquidación.</p>
      )}

      {/* KPI Cards */}
      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Total sin factura">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Total sin factura</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{formatCurrency(data.total_sin_factura)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Total con factura">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Total con factura</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{formatCurrency(data.total_con_factura)}</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200">
              <nav className="flex" aria-label="Segmentos de liquidación">
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    aria-selected={activeTab === tab.id}
                    role="tab"
                    className={[
                      'px-6 py-3 text-sm font-medium transition-colors',
                      activeTab === tab.id
                        ? 'border-b-2 border-indigo-600 text-indigo-600'
                        : 'text-slate-500 hover:text-slate-700',
                    ].join(' ')}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
            <div role="tabpanel">
              <SegmentoTab docentes={data[activeTab]} />
            </div>
          </div>
        </>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={confirmOpen}
        title={`Cerrar liquidación ${filters.periodo}`}
        message="Esta acción es irreversible. Una vez cerrada, la liquidación no puede modificarse. ¿Confirma el cierre?"
        confirmLabel="Cerrar liquidación"
        isLoading={cerrarMutation.isPending}
        onConfirm={handleCerrar}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  )
}
