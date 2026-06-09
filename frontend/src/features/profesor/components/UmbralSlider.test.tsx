import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UmbralSlider } from './UmbralSlider'

describe('UmbralSlider', () => {
  it('renderiza con el valor inicial correcto', () => {
    render(<UmbralSlider value={60} onChange={vi.fn()} />)

    const numberInput = screen.getByRole('spinbutton')
    expect(numberInput).toHaveValue(60)

    const slider = screen.getByRole('slider')
    expect(slider).toHaveValue('60')
  })

  it('muestra el label de umbral', () => {
    render(<UmbralSlider value={75} onChange={vi.fn()} />)

    expect(screen.getByText('Umbral:')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('llama a onChange cuando se cambia el número y se hace blur', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<UmbralSlider value={60} onChange={onChange} />)

    const numberInput = screen.getByRole('spinbutton')
    await user.clear(numberInput)
    await user.type(numberInput, '80')
    await user.tab() // triggers blur

    expect(onChange).toHaveBeenCalled()
  })

  it('muestra "Guardando..." cuando isLoading es true', () => {
    render(<UmbralSlider value={60} onChange={vi.fn()} isLoading />)

    expect(screen.getByText('Guardando...')).toBeInTheDocument()
  })

  it('el slider y el input numérico están deshabilitados cuando isLoading es true', () => {
    render(<UmbralSlider value={60} onChange={vi.fn()} isLoading />)

    expect(screen.getByRole('slider')).toBeDisabled()
    expect(screen.getByRole('spinbutton')).toBeDisabled()
  })
})
