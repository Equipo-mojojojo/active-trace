import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { ListaDestinatarios } from '../components/ListaDestinatarios'
import { PreviewMensaje } from '../components/PreviewMensaje'
import { Button } from '@/shared/components/ui/Button'
import { comunicacionesService } from '../services/comunicacionesService'
import type {
  ComunicacionPreviewResponse,
  ComunicacionPreviewRequest,
} from '../types/profesor.types'

const DEFAULT_ASUNTO = 'Aviso sobre tu situación académica en {materia}'
const DEFAULT_CUERPO =
  'Estimado/a {nombre},\n\nTe informamos que estás en condición de atrasado/a en las actividades de {materia}.\n\nPor favor, ponete en contacto con tu docente para regularizar tu situación.\n\nSaludos,\nEquipo Docente'

interface LocationState {
  destinatariosIds?: string[]
}

/**
 * Pantalla de comunicación a atrasados.
 * Layout 2 columnas: ListaDestinatarios | PreviewMensaje.
 */
export function ComunicacionPage() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | undefined

  const [seleccionados, setSeleccionados] = useState<string[]>(
    state?.destinatariosIds ?? [],
  )
  const [asuntoTemplate, setAsuntoTemplate] = useState(DEFAULT_ASUNTO)
  const [cuerpoTemplate, setCuerpoTemplate] = useState(DEFAULT_CUERPO)
  const [preview, setPreview] = useState<ComunicacionPreviewResponse | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)

  const previewMutation = useMutation({
    mutationFn: (payload: ComunicacionPreviewRequest) =>
      comunicacionesService.getPreviewMensaje(payload),
    onSuccess: (data) => {
      setPreview(data)
      setPreviewError(null)
    },
    onError: (err: Error) => setPreviewError(err.message),
  })

  const enviarMutation = useMutation({
    mutationFn: (payload: ComunicacionPreviewRequest) =>
      comunicacionesService.enviarComunicacion(payload),
    onSuccess: (data) => {
      navigate('/profesor/comunicacion/tracking', {
        state: { loteId: data.lote_id },
      })
    },
  })

  // Fetch preview whenever seleccionados or templates change
  useEffect(() => {
    if (!comisionId || seleccionados.length === 0) return
    const payload: ComunicacionPreviewRequest = {
      materia_id: comisionId,
      entrada_padron_ids: seleccionados,
      asunto_template: asuntoTemplate,
      cuerpo_template: cuerpoTemplate,
    }
    previewMutation.mutate(payload)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seleccionados, asuntoTemplate, cuerpoTemplate, comisionId])

  const handleToggle = (id: string) => {
    setSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    )
  }

  const handleToggleAll = () => {
    if (!preview) return
    const allIds = preview.preview.map((p) => p.entrada_padron_id)
    const allSelected = allIds.every((id) => seleccionados.includes(id))
    setSeleccionados(allSelected ? [] : allIds)
  }

  const handleEnviar = () => {
    if (!comisionId || seleccionados.length === 0) return
    enviarMutation.mutate({
      materia_id: comisionId,
      entrada_padron_ids: seleccionados,
      asunto_template: asuntoTemplate,
      cuerpo_template: cuerpoTemplate,
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          ← Volver
        </button>
        <h1 className="text-2xl font-semibold text-slate-900">Enviar Comunicación</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left column: Destinatarios */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <ListaDestinatarios
            destinatarios={preview?.preview ?? []}
            seleccionados={seleccionados}
            onToggle={handleToggle}
            onToggleAll={handleToggleAll}
          />
        </div>

        {/* Right column: Preview */}
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <PreviewMensaje
            previews={preview?.preview ?? []}
            asuntoTemplate={asuntoTemplate}
            cuerpoTemplate={cuerpoTemplate}
            requiereAprobacion={preview?.requiere_aprobacion}
            onAsuntoChange={setAsuntoTemplate}
            onCuerpoChange={setCuerpoTemplate}
          />
        </div>
      </div>

      {previewError && (
        <p className="text-sm text-red-600">{previewError}</p>
      )}

      {enviarMutation.isError && (
        <p className="text-sm text-red-600">
          Error al enviar: {(enviarMutation.error as Error).message}. Podés reintentar.
        </p>
      )}

      <div className="flex justify-end gap-3">
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Cancelar
        </Button>
        <Button
          onClick={handleEnviar}
          isLoading={enviarMutation.isPending}
          disabled={seleccionados.length === 0}
          aria-label={
            seleccionados.length === 0
              ? 'Seleccioná al menos un destinatario para enviar'
              : 'Enviar comunicación'
          }
        >
          {preview?.requiere_aprobacion
            ? 'Enviar para aprobación'
            : `Enviar a ${seleccionados.length} destinatario${seleccionados.length !== 1 ? 's' : ''}`}
        </Button>
      </div>

      {seleccionados.length === 0 && (
        <p className="text-center text-sm text-slate-500" role="status">
          Seleccioná al menos un destinatario para habilitar el envío.
        </p>
      )}
    </div>
  )
}
