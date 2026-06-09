import type { ComunicacionPreviewItem } from '../types/profesor.types'

interface PreviewMensajeProps {
  previews: ComunicacionPreviewItem[]
  asuntoTemplate: string
  cuerpoTemplate: string
  requiereAprobacion?: boolean
  onAsuntoChange: (value: string) => void
  onCuerpoChange: (value: string) => void
}

/**
 * Panel derecho del flujo de comunicación.
 * Muestra asunto editable, cuerpo del mensaje y badge condicional de aprobación.
 */
export function PreviewMensaje({
  previews,
  asuntoTemplate,
  cuerpoTemplate,
  requiereAprobacion = false,
  onAsuntoChange,
  onCuerpoChange,
}: PreviewMensajeProps) {
  const firstPreview = previews[0]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Preview del mensaje</h3>
        {requiereAprobacion && (
          <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800">
            Requiere aprobación
          </span>
        )}
      </div>

      {/* Editable subject */}
      <div>
        <label htmlFor="asunto-template" className="mb-1 block text-xs font-medium text-slate-700">
          Asunto
        </label>
        <input
          id="asunto-template"
          type="text"
          value={asuntoTemplate}
          onChange={(e) => onAsuntoChange(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Asunto del mensaje..."
        />
      </div>

      {/* Editable body */}
      <div>
        <label htmlFor="cuerpo-template" className="mb-1 block text-xs font-medium text-slate-700">
          Cuerpo del mensaje
        </label>
        <textarea
          id="cuerpo-template"
          value={cuerpoTemplate}
          onChange={(e) => onCuerpoChange(e.target.value)}
          rows={6}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Cuerpo del mensaje..."
        />
      </div>

      {/* Preview for first recipient */}
      {firstPreview && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="mb-2 text-xs font-medium uppercase text-slate-500">
            Preview para: {firstPreview.destinatario_nombre}
          </p>
          <p className="mb-1 text-sm font-medium text-slate-900">{firstPreview.asunto}</p>
          <p className="text-sm text-slate-600 whitespace-pre-wrap">{firstPreview.cuerpo}</p>
        </div>
      )}
    </div>
  )
}
