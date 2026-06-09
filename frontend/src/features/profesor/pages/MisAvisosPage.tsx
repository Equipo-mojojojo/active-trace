import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { avisosService } from '@/features/coordinacion/services/avisosService'

const SEVERIDAD_STYLES: Record<string, string> = {
  Info: 'bg-blue-100 text-blue-700',
  Advertencia: 'bg-yellow-100 text-yellow-700',
  Crítico: 'bg-red-100 text-red-700',
}

export function MisAvisosPage() {
  const queryClient = useQueryClient()
  const [ackingId, setAckingId] = useState<string | null>(null)

  const { data: avisos = [], isLoading, isError } = useQuery({
    queryKey: ['mis-avisos'],
    queryFn: avisosService.getMisAvisos,
  })

  const ackMutation = useMutation({
    mutationFn: (id: string) => avisosService.ackAviso(id),
    onMutate: (id) => setAckingId(id),
    onSettled: () => {
      setAckingId(null)
      queryClient.invalidateQueries({ queryKey: ['mis-avisos'] })
    },
  })

  const activos = avisos.filter((a) => a.activo)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Mis Avisos</h1>
        <p className="mt-1 text-sm text-slate-500">
          Avisos institucionales publicados para tu rol.
        </p>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Cargando avisos...</p>}
      {isError && <p className="text-sm text-red-600">Error al cargar los avisos.</p>}

      {!isLoading && activos.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-200 py-12 text-center">
          <p className="text-sm text-slate-400">No hay avisos activos para tu rol.</p>
        </div>
      )}

      <div className="space-y-3">
        {activos.map((aviso) => (
          <div
            key={aviso.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">{aviso.titulo}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERIDAD_STYLES[aviso.severidad] ?? 'bg-slate-100 text-slate-600'}`}
                  >
                    {aviso.severidad}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                    {aviso.alcance}
                  </span>
                </div>
                {aviso.cuerpo && (
                  <p className="text-sm text-slate-600">{aviso.cuerpo}</p>
                )}
                <p className="text-xs text-slate-400">
                  Desde: {new Date(aviso.vigencia_desde).toLocaleDateString('es-AR')}
                  {aviso.vigencia_hasta &&
                    ` — Hasta: ${new Date(aviso.vigencia_hasta).toLocaleDateString('es-AR')}`}
                </p>
              </div>

              {aviso.requiere_ack && (
                <button
                  onClick={() => ackMutation.mutate(aviso.id)}
                  disabled={ackingId === aviso.id}
                  className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  {ackingId === aviso.id ? 'Confirmando...' : 'Confirmar lectura'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
