import { useRef, useState } from 'react'
import type { DragEvent, ChangeEvent } from 'react'

interface DropzoneUploadProps {
  onFile: (file: File) => void
  isLoading?: boolean
  accept?: string[]
}

/**
 * Drag-and-drop file upload zone using native HTML5 drag events.
 * Accepts CSV/XLSX files. Falls back to file input click.
 */
export function DropzoneUpload({
  onFile,
  isLoading = false,
  accept = ['.csv', '.xlsx', '.xls'],
}: DropzoneUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateAndProcess = (file: File) => {
    const ext = file.name.toLowerCase().split('.').pop()
    if (!ext || !['csv', 'xlsx', 'xls'].includes(ext)) {
      setError('Formato no soportado. Usá CSV o Excel (.csv, .xlsx, .xls).')
      return
    }
    setError(null)
    onFile(file)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) validateAndProcess(file)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) validateAndProcess(file)
  }

  return (
    <div className="space-y-2">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isLoading && inputRef.current?.click()}
        role="button"
        aria-label="Zona de carga de archivo. Arrastrá un archivo CSV o Excel, o hacé clic para seleccionar."
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        className={[
          'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors',
          isDragging
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50',
          isLoading ? 'pointer-events-none opacity-60' : '',
        ].join(' ')}
      >
        <svg
          className="mb-3 h-10 w-10 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        <p className="text-sm font-medium text-slate-700">
          {isLoading ? 'Procesando archivo...' : 'Arrastrá tu archivo acá o hacé clic'}
        </p>
        <p className="mt-1 text-xs text-slate-400">
          {accept.join(', ')} — hasta 10 MB
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept.join(',')}
        onChange={handleInputChange}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      />

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
