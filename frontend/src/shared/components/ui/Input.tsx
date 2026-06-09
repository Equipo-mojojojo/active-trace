import type { InputHTMLAttributes } from 'react'
import { forwardRef } from 'react'

type InputProps = InputHTMLAttributes<HTMLInputElement>

const inputClasses =
  'block w-full rounded-md border-slate-300 shadow-sm ' +
  'focus:border-primary-500 focus:ring-primary-500 sm:text-sm ' +
  'disabled:bg-slate-50 disabled:text-slate-500'

/**
 * Styled input compatible with React Hook Form's {...register(...)}.
 * Uses forwardRef so RHF can manage focus/value correctly.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`${inputClasses} ${className ?? ''}`}
        {...props}
      />
    )
  },
)

Input.displayName = 'Input'
