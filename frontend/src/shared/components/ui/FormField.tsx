import type { ReactNode } from 'react'

interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  children: ReactNode
  htmlFor?: string
  labelClassName?: string
}

export function FormField({
  label,
  error,
  required = false,
  children,
  htmlFor,
  labelClassName,
}: FormFieldProps) {
  return (
    <div className="space-y-1">
      <label
        htmlFor={htmlFor}
        className={`block text-sm font-medium ${labelClassName ?? 'text-slate-700'}`}
      >
        {label}
        {required && <span className="ml-1 text-red-500" aria-hidden="true">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
