import { useParams, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { TabsComision } from '../components/TabsComision'
import { UmbralSlider } from '../components/UmbralSlider'
import { comisionesService } from '../services/comisionesService'

/**
 * Hub de la comisión del profesor.
 * Muestra UmbralSlider + TabsComision con los 4 tabs de análisis.
 * El materiaId se obtiene del param comisionId (en el dominio actual, comisionId == materiaId).
 */
export function ComisionPage() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()
  const [umbral, setUmbral] = useState(60)

  const umbralMutation = useMutation({
    mutationFn: (newUmbral: number) =>
      comisionesService.configurarUmbral({
        asignacion_id: comisionId ?? '',
        materia_id: comisionId ?? '',
        umbral_pct: newUmbral,
        valores_aprobatorios: [],
      }),
    onSuccess: (data) => setUmbral(data.umbral_pct),
  })

  const handleComunicar = (seleccionados: string[]) => {
    if (seleccionados.length === 0) return
    navigate(`/profesor/comunicacion/${comisionId}`, {
      state: { destinatariosIds: seleccionados },
    })
  }

  if (!comisionId) {
    return <p className="text-red-600">Comisión no encontrada.</p>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Comisión</h1>
          <p className="text-sm text-slate-500">ID: {comisionId}</p>
        </div>
        <button
          onClick={() => navigate(`/profesor/comisiones/${comisionId}/importar`)}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Importar calificaciones
        </button>
      </div>

      {/* Umbral */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <p className="mb-3 text-sm font-medium text-slate-700">Umbral de aprobación</p>
        <UmbralSlider
          value={umbral}
          onChange={(v) => umbralMutation.mutate(v)}
          isLoading={umbralMutation.isPending}
        />
      </div>

      {/* Tabs */}
      <TabsComision materiaId={comisionId} onComunicar={handleComunicar} />
    </div>
  )
}
