import { useState } from 'react'

interface UmbralSliderProps {
  value: number
  onChange: (value: number) => void
  isLoading?: boolean
}

/**
 * Slider numérico para configurar el umbral de aprobación (%).
 * Controlado; llama `onChange` cuando el usuario suelta el slider o hace blur.
 */
export function UmbralSlider({ value, onChange, isLoading = false }: UmbralSliderProps) {
  const [localValue, setLocalValue] = useState(value)

  const handleCommit = () => {
    if (localValue !== value) {
      onChange(localValue)
    }
  }

  return (
    <div className="flex items-center gap-4">
      <label htmlFor="umbral-slider" className="text-sm font-medium text-slate-700 whitespace-nowrap">
        Umbral:
      </label>
      <input
        id="umbral-slider"
        type="range"
        min={0}
        max={100}
        step={5}
        value={localValue}
        onChange={(e) => setLocalValue(Number(e.target.value))}
        onMouseUp={handleCommit}
        onTouchEnd={handleCommit}
        onKeyUp={handleCommit}
        disabled={isLoading}
        className="h-2 w-40 cursor-pointer accent-indigo-600 disabled:opacity-50"
        aria-label={`Umbral de aprobación: ${localValue}%`}
      />
      <input
        type="number"
        min={0}
        max={100}
        value={localValue}
        onChange={(e) => setLocalValue(Number(e.target.value))}
        onBlur={handleCommit}
        disabled={isLoading}
        className="w-16 rounded-md border border-slate-300 px-2 py-1 text-center text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-label="Umbral numérico"
      />
      <span className="text-sm text-slate-500">%</span>
      {isLoading && (
        <span className="text-xs text-slate-400">Guardando...</span>
      )}
    </div>
  )
}
