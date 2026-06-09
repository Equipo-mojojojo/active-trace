/**
 * FilaEditable — fila de tabla con modo edición inline.
 * Soporta date-range de vigencia (hasta opcional/abierta).
 * Maneja error 409 inline conservando los datos ingresados.
 */
import { useState } from 'react'
import type { ReactNode } from 'react'

export interface FilaField {
  key: string
  label: string
  type?: 'text' | 'number' | 'date' | 'select'
  options?: { value: string; label: string }[]
  required?: boolean
}

interface FilaEditableProps {
  fields: FilaField[]
  initialValues: Record<string, string>
  displayRow: ReactNode
  onSave: (values: Record<string, string>) => Promise<void>
  onDelete?: () => Promise<void>
  isDeleting?: boolean
  /** Start in edit mode immediately (e.g. for new rows) */
  startEditing?: boolean
}

export function FilaEditable({
  fields,
  initialValues,
  displayRow,
  onSave,
  onDelete,
  isDeleting = false,
  startEditing = false,
}: FilaEditableProps) {
  const [editing, setEditing] = useState(startEditing)
  const [values, setValues] = useState<Record<string, string>>(initialValues)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setError(null)
    setSaving(true)
    try {
      await onSave(values)
      setEditing(false)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axErr = err as { response?: { status?: number } }
        if (axErr.response?.status === 409) {
          setError('Solapamiento de vigencia: ya existe un registro para ese período.')
        } else {
          setError('Error al guardar.')
        }
      } else {
        setError('Error al guardar.')
      }
      // Preserve values on error (do NOT reset)
    } finally {
      setSaving(false)
    }
  }

  if (!editing) {
    return (
      <tr className="hover:bg-slate-50">
        {displayRow}
        <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
          <button
            type="button"
            onClick={() => {
              setValues(initialValues)
              setError(null)
              setEditing(true)
            }}
            className="mr-2 text-indigo-600 hover:underline"
          >
            Editar
          </button>
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              disabled={isDeleting}
              className="text-red-600 hover:underline disabled:opacity-50"
            >
              {isDeleting ? '...' : 'Eliminar'}
            </button>
          )}
        </td>
      </tr>
    )
  }

  return (
    <>
      <tr className="bg-indigo-50">
        {fields.map((field) => (
          <td key={field.key} className="px-4 py-2">
            {field.type === 'select' ? (
              <select
                value={values[field.key] ?? ''}
                onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
                className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">— Seleccionar —</option>
                {field.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ) : (
              <input
                type={field.type ?? 'text'}
                value={values[field.key] ?? ''}
                onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
                placeholder={field.label}
                className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            )}
          </td>
        ))}
        <td className="whitespace-nowrap px-4 py-2 text-right text-sm">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="mr-2 rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
          <button
            type="button"
            onClick={() => { setEditing(false); setError(null) }}
            className="text-slate-500 hover:underline text-xs"
          >
            Cancelar
          </button>
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={fields.length + 1} className="bg-red-50 px-4 py-1 text-xs text-red-700">
            {error}
          </td>
        </tr>
      )}
    </>
  )
}
