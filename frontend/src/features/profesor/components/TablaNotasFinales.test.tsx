import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TablaNotasFinales } from './TablaNotasFinales'
import type { NotaFinalEntry } from '../types/profesor.types'

const mockNotas: NotaFinalEntry[] = [
  { entrada_padron_id: 'ep-1', nombre: 'Ana', apellidos: 'Lopez', nota_final: 8.5 },
  { entrada_padron_id: 'ep-2', nombre: 'Juan', apellidos: 'Perez', nota_final: 7.0 },
]

describe('TablaNotasFinales', () => {
  it('renderiza la tabla con notas finales', () => {
    render(<TablaNotasFinales notas={mockNotas} />)

    expect(screen.getByText('Lopez, Ana')).toBeInTheDocument()
    expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    expect(screen.getByText('8.50')).toBeInTheDocument()
    expect(screen.getByText('7.00')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay notas', () => {
    render(<TablaNotasFinales notas={[]} />)

    expect(screen.getByText(/no hay notas finales/i)).toBeInTheDocument()
  })

  it('muestra el botón de exportar cuando se provee onExport', async () => {
    const user = userEvent.setup()
    const onExport = vi.fn()

    render(<TablaNotasFinales notas={mockNotas} onExport={onExport} />)

    const exportBtn = screen.getByText('Exportar CSV')
    await user.click(exportBtn)

    expect(onExport).toHaveBeenCalledOnce()
  })

  it('muestra las actividades seleccionadas cuando se proveen', () => {
    render(
      <TablaNotasFinales
        notas={mockNotas}
        actividadesSeleccionadas={['TP1', 'TP2']}
      />,
    )

    expect(screen.getByText(/actividades consideradas/i)).toBeInTheDocument()
    expect(screen.getByText('TP1, TP2')).toBeInTheDocument()
  })
})
