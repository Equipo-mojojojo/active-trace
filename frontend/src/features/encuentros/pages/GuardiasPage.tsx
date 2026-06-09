/**
 * GuardiasPage — consulta y exportación de guardias.
 */
import { useState } from 'react'
import { useGuardias } from '../hooks/useGuardias'
import { encuentrosService } from '../services/encuentrosService'
import { TablaGuardias } from '../components/TablaGuardias'
import type { GuardiasFilters } from '../types/encuentros.types'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function GuardiasPage() {
  const [filters, setFilters] = useState<GuardiasFilters>({})

  const guardiasQuery = useGuardias(filters)

  const handleExport = async () => {
    const blob = await encuentrosService.exportGuardias(filters)
    downloadBlob(blob, 'guardias.csv')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Guardias</h1>
        <p className="mt-1 text-sm text-slate-500">Registro de guardias de tutores</p>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Período desde</label>
          <input
            type="date"
            value={filters.periodo_desde ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, periodo_desde: e.target.value || undefined }))
            }
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Período hasta</label>
          <input
            type="date"
            value={filters.periodo_hasta ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, periodo_hasta: e.target.value || undefined }))
            }
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Docente (ID)</label>
          <input
            type="text"
            placeholder="UUID de asignación"
            value={filters.docente ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, docente: e.target.value || undefined }))
            }
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Tabla */}
      {guardiasQuery.isLoading && <p className="text-sm text-slate-500">Cargando guardias...</p>}
      {guardiasQuery.isError && <p className="text-sm text-red-600">Error al cargar las guardias.</p>}
      {!guardiasQuery.isLoading && (
        <TablaGuardias guardias={guardiasQuery.data ?? []} onExport={handleExport} />
      )}
    </div>
  )
}
