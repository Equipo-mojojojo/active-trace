/**
 * HiloComentarios — lista scrollable de comentarios + campo agregar.
 *
 * Diseño (from Stitch screen 8d5c3c2e698c428ca2dead29ddbaea84):
 *  - Lista de comentarios: avatar inicial, autor_id (abreviado), fecha, texto
 *  - Campo de texto "Agregar comentario" + botón Enviar
 */
import { useState } from 'react'
import { useComentariosTarea, useAddComentario } from '../hooks/useTareas'

interface Props {
  tareaId: string
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function HiloComentarios({ tareaId }: Props) {
  const [texto, setTexto] = useState('')
  const comentariosQuery = useComentariosTarea(tareaId)
  const addMutation = useAddComentario()

  const handleSend = async () => {
    const trimmed = texto.trim()
    if (!trimmed) return
    await addMutation.mutateAsync({ tareaId, texto: trimmed })
    setTexto('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      void handleSend()
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-slate-700">Comentarios</h3>

      {/* Lista */}
      <div className="max-h-64 space-y-3 overflow-y-auto">
        {comentariosQuery.isLoading && (
          <p className="text-xs text-slate-400">Cargando comentarios...</p>
        )}
        {!comentariosQuery.isLoading && (comentariosQuery.data ?? []).length === 0 && (
          <p className="text-xs text-slate-400">Sin comentarios todavía.</p>
        )}
        {(comentariosQuery.data ?? []).map((c) => (
          <div key={c.id} className="flex gap-3">
            {/* Avatar inicial */}
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
              {c.autor_id.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-xs font-semibold text-slate-700 font-mono">
                  {c.autor_id.slice(0, 8)}…
                </p>
                <p className="text-xs text-slate-400">{formatDate(c.creado_at)}</p>
              </div>
              <p className="mt-0.5 text-sm text-slate-600">{c.texto}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Campo agregar */}
      <div className="flex flex-col gap-2">
        <textarea
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Agregar comentario... (Ctrl+Enter para enviar)"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="button"
          onClick={() => void handleSend()}
          disabled={!texto.trim() || addMutation.isPending}
          className="self-end rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {addMutation.isPending ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  )
}
