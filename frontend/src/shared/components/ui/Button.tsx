import type { ButtonHTMLAttributes, ReactNode } from 'react'

// ─── Types ───────────────────────────────────────────────────────────────────

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  isLoading?: boolean
  children: ReactNode
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
  secondary:
    'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus:ring-primary-500',
  ghost: 'text-slate-600 hover:bg-slate-100 focus:ring-slate-400',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
}

const baseClasses =
  'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium ' +
  'focus:outline-none focus:ring-2 focus:ring-offset-2 ' +
  'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'

// ─── Spinner ─────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

// ─── Component ───────────────────────────────────────────────────────────────

export function Button({
  variant = 'primary',
  isLoading = false,
  children,
  disabled,
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className ?? ''}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && <Spinner />}
      {children}
    </button>
  )
}
