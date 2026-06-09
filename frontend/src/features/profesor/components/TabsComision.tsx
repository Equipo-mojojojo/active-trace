import { useState } from 'react'
import { TablaAtrasados } from './TablaAtrasados'
import { TablaRanking } from './TablaRanking'
import { TablaNotasFinales } from './TablaNotasFinales'
import { useAtrasados } from '../hooks/useAtrasados'
import { useRanking } from '../hooks/useRanking'
import { useNotasFinales } from '../hooks/useNotasFinales'
import { comisionesService } from '../services/comisionesService'

type TabId = 'atrasados' | 'ranking' | 'notas-finales' | 'sin-corregir'

interface TabsComisionProps {
  materiaId: string
  onComunicar?: (seleccionados: string[]) => void
}

const TABS: { id: TabId; label: string }[] = [
  { id: 'atrasados', label: 'Atrasados' },
  { id: 'ranking', label: 'Ranking' },
  { id: 'notas-finales', label: 'Notas Finales' },
  { id: 'sin-corregir', label: 'Sin corregir' },
]

export function TabsComision({ materiaId, onComunicar }: TabsComisionProps) {
  const [activeTab, setActiveTab] = useState<TabId>('atrasados')
  const [seleccionados, setSeleccionados] = useState<string[]>([])
  const [isExporting, setIsExporting] = useState(false)

  const atrasadosQuery = useAtrasados(materiaId)
  const rankingQuery = useRanking(materiaId)
  const notasQuery = useNotasFinales(materiaId)

  const toggleSeleccion = (id: string) => {
    setSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    )
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const blob = await comisionesService.exportSinCorregir(materiaId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sin_corregir_${materiaId}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Tab nav */}
      <div className="flex border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={[
              'px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.id
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-slate-500 hover:text-slate-700',
            ].join(' ')}
            aria-selected={activeTab === tab.id}
            role="tab"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      {activeTab === 'atrasados' && (
        <div role="tabpanel">
          {atrasadosQuery.isLoading && (
            <p className="text-sm text-slate-500">Cargando atrasados...</p>
          )}
          {atrasadosQuery.isError && (
            <p className="text-sm text-red-600">Error al cargar los datos.</p>
          )}
          {atrasadosQuery.data && (
            <TablaAtrasados
              atrasados={atrasadosQuery.data.atrasados}
              seleccionados={seleccionados}
              onToggleSeleccion={toggleSeleccion}
              onComunicar={
                onComunicar ? () => onComunicar(seleccionados) : undefined
              }
            />
          )}
        </div>
      )}

      {activeTab === 'ranking' && (
        <div role="tabpanel">
          {rankingQuery.isLoading && (
            <p className="text-sm text-slate-500">Cargando ranking...</p>
          )}
          {rankingQuery.isError && (
            <p className="text-sm text-red-600">Error al cargar el ranking.</p>
          )}
          {rankingQuery.data && (
            <TablaRanking ranking={rankingQuery.data.ranking} />
          )}
        </div>
      )}

      {activeTab === 'notas-finales' && (
        <div role="tabpanel">
          {notasQuery.isLoading && (
            <p className="text-sm text-slate-500">Cargando notas finales...</p>
          )}
          {notasQuery.isError && (
            <p className="text-sm text-red-600">Error al cargar las notas.</p>
          )}
          {notasQuery.data && (
            <TablaNotasFinales
              notas={notasQuery.data.notas}
              actividadesSeleccionadas={notasQuery.data.actividades_seleccionadas}
            />
          )}
        </div>
      )}

      {activeTab === 'sin-corregir' && (
        <div role="tabpanel">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-900">
                Entregas pendientes de corrección
              </h3>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                {isExporting ? 'Exportando...' : 'Exportar CSV'}
              </button>
            </div>
            <p className="text-sm text-slate-500">
              Descargá el CSV con las entregas detectadas como pendientes de corrección.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
