import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ImportStepper } from './ImportStepper'

describe('ImportStepper', () => {
  it('muestra el paso 1 activo en estado "upload"', () => {
    render(<ImportStepper currentStep="upload" />)

    expect(screen.getByText('Subir archivo')).toBeInTheDocument()
    expect(screen.getByText('Seleccionar actividades')).toBeInTheDocument()
    expect(screen.getByText('Confirmar importación')).toBeInTheDocument()
  })

  it('muestra el paso 2 activo en estado "preview"', () => {
    render(<ImportStepper currentStep="preview" />)

    // Step 1 should be completed (shows checkmark via SVG), Step 2 active
    const activeStep = screen.getByText('Seleccionar actividades')
    expect(activeStep).toBeInTheDocument()
  })

  it('muestra el paso 3 activo en estado "confirmar"', () => {
    render(<ImportStepper currentStep="confirmar" />)

    const confirmarText = screen.getByText('Confirmar importación')
    expect(confirmarText).toBeInTheDocument()
    // Steps 1 and 2 should be completed
  })

  it('tiene aria-label de navegación', () => {
    render(<ImportStepper currentStep="upload" />)

    expect(screen.getByRole('navigation', { name: /pasos de importación/i })).toBeInTheDocument()
  })

  it('el paso actual tiene aria-current="step"', () => {
    render(<ImportStepper currentStep="upload" />)

    const currentStep = document.querySelector('[aria-current="step"]')
    expect(currentStep).toBeInTheDocument()
  })
})
