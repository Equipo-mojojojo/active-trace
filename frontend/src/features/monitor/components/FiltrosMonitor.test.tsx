import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FiltrosMonitor } from './FiltrosMonitor'

describe('FiltrosMonitor', () => {
  it('renderiza todos los campos de filtro', () => {
    render(<FiltrosMonitor filtros={{}} onChange={vi.fn()} />)

    expect(screen.getByPlaceholderText(/nombre o correo/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ej: a, b/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ej: 5/i)).toBeInTheDocument()
    expect(screen.getByText('Limpiar filtros')).toBeInTheDocument()
  })

  it('llama a onChange con el nuevo q cuando se escribe en búsqueda', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<FiltrosMonitor filtros={{}} onChange={onChange} />)

    const qInput = screen.getByPlaceholderText(/nombre o correo/i)
    await user.type(qInput, 'Juan')

    // Each character triggers onChange
    expect(onChange).toHaveBeenCalled()
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
    expect(lastCall).toHaveProperty('q', 'Juan')
  })

  it('llama a onChange con la comisión cuando se selecciona', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<FiltrosMonitor filtros={{}} onChange={onChange} />)

    const comisionInput = screen.getByPlaceholderText(/ej: a, b/i)
    await user.type(comisionInput, 'A')

    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
    expect(lastCall).toHaveProperty('comision', 'A')
  })

  it('llama a onChange con min_aprobadas cuando se ingresa un número', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<FiltrosMonitor filtros={{}} onChange={onChange} />)

    const minInput = screen.getByPlaceholderText(/ej: 5/i)
    await user.type(minInput, '5')

    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
    expect(lastCall).toHaveProperty('min_aprobadas', 5)
  })

  it('resetea todos los filtros al hacer clic en Limpiar filtros', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<FiltrosMonitor filtros={{ q: 'Juan', comision: 'A' }} onChange={onChange} />)

    await user.click(screen.getByText('Limpiar filtros'))

    expect(onChange).toHaveBeenCalledWith({})
  })
})