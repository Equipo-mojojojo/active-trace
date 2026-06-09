import type { ComunicacionPreviewItem } from '../types/profesor.types'

interface ListaDestinatariosProps {
  destinatarios: ComunicacionPreviewItem[]
  seleccionados: string[]
  onToggle: (id: string) => void
  onToggleAll: () => void
}

/**
 * Lista scrollable de destinatarios con checkbox individual.
 * Muestra contador y opción "seleccionar todos".
 */
export function ListaDestinatarios({
  destinatarios,
  seleccionados,
  onToggle,
  onToggleAll,
}: ListaDestinatariosProps) {
  const allSelected = destinatarios.length > 0 && seleccionados.length === destinatarios.length
  const count = seleccionados.length

  return (
    <div className="flex flex-col h-full">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Destinatarios</h3>
        <span className="text-xs text-slate-500">
          {count} seleccionado{count !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Toggle all */}
      <div className="mb-2 flex items-center gap-2 border-b border-slate-100 pb-2">
        <input
          id="toggle-all"
          type="checkbox"
          checked={allSelected}
          onChange={onToggleAll}
          className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
        />
        <label htmlFor="toggle-all" className="text-sm text-slate-600 cursor-pointer">
          Seleccionar todos
        </label>
      </div>

      {/* List */}
      <ul className="flex-1 overflow-y-auto space-y-1 max-h-96">
        {destinatarios.map((dest) => {
          const isChecked = seleccionados.includes(dest.entrada_padron_id)
          return (
            <li key={dest.entrada_padron_id}>
              <label className="flex cursor-pointer items-start gap-3 rounded-md p-2 hover:bg-slate-50">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => onToggle(dest.entrada_padron_id)}
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900">
                    {dest.destinatario_nombre}
                  </p>
                  <p className="truncate text-xs text-slate-500">{dest.destinatario_email}</p>
                </div>
              </label>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
