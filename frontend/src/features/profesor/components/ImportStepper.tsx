type StepStatus = 'pending' | 'active' | 'completed'

interface Step {
  id: number
  label: string
}

interface ImportStepperProps {
  currentStep: 'upload' | 'preview' | 'confirmar'
}

const STEPS: Step[] = [
  { id: 1, label: 'Subir archivo' },
  { id: 2, label: 'Seleccionar actividades' },
  { id: 3, label: 'Confirmar importación' },
]

const STEP_MAP: Record<ImportStepperProps['currentStep'], number> = {
  upload: 1,
  preview: 2,
  confirmar: 3,
}

function getStatus(stepId: number, currentStepNum: number): StepStatus {
  if (stepId < currentStepNum) return 'completed'
  if (stepId === currentStepNum) return 'active'
  return 'pending'
}

export function ImportStepper({ currentStep }: ImportStepperProps) {
  const currentStepNum = STEP_MAP[currentStep]

  return (
    <nav aria-label="Pasos de importación" className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((step, idx) => {
          const status = getStatus(step.id, currentStepNum)

          return (
            <li key={step.id} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  aria-current={status === 'active' ? 'step' : undefined}
                  className={[
                    'flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors',
                    status === 'completed'
                      ? 'bg-indigo-600 text-white'
                      : status === 'active'
                        ? 'border-2 border-indigo-600 bg-white text-indigo-600'
                        : 'border-2 border-slate-300 bg-white text-slate-400',
                  ].join(' ')}
                >
                  {status === 'completed' ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </div>
                <span
                  className={[
                    'mt-2 text-xs font-medium',
                    status === 'active' ? 'text-indigo-600' : 'text-slate-500',
                  ].join(' ')}
                >
                  {step.label}
                </span>
              </div>

              {idx < STEPS.length - 1 && (
                <div
                  className={[
                    'mx-2 h-0.5 flex-1 transition-colors',
                    step.id < currentStepNum ? 'bg-indigo-600' : 'bg-slate-200',
                  ].join(' ')}
                  aria-hidden="true"
                />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
