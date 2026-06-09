/**
 * Tests for TablaAtrasados.
 * TDD: tests written before implementation.
 *
 * Scenarios:
 * - Renderiza filas con badge "Atrasado"
 * - Muestra estado vacío cuando no hay atrasados
 * - Checkbox de selección funciona
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TablaAtrasados } from './TablaAtrasados'
import type { AlumnoAtrasado } from '../types/profesor.types'

const mockAtrasados: AlumnoAtrasado[] = [
  {
    entrada_padron_id: 'ep-1',
    nombre: 'Juan',
    apellidos: 'Perez',
    comision: 'A',
    materia_id: 'mat-1',
    actividades_faltantes: ['TP1', 'TP2'],
    actividades_reprobadas: [],
  },
  {
    entrada_padron_id: 'ep-2',
    nombre: 'Maria',
    apellidos: 'Garcia',
    comision: 'A',
    materia_id: 'mat-1',
    actividades_faltantes: ['TP3'],
    actividades_reprobadas: ['TP1'],
  },
]

describe('TablaAtrasados', () => {
  it('renderiza filas con badge "Atrasado" para cada alumno', () => {
    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={[]}
        onToggleSeleccion={vi.fn()}
      />,
    )

    const rows = screen.getAllByTestId('atrasado-row')
    expect(rows).toHaveLength(2)

    // Nombres
    expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    expect(screen.getByText('Garcia, Maria')).toBeInTheDocument()

    // Badges de estado
    const badges = screen.getAllByText('Atrasado')
    expect(badges).toHaveLength(2)
  })

  it('muestra actividades faltantes en cada fila', () => {
    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={[]}
        onToggleSeleccion={vi.fn()}
      />,
    )

    expect(screen.getByText('TP1, TP2')).toBeInTheDocument()
    expect(screen.getByText('TP3')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay atrasados', () => {
    render(
      <TablaAtrasados
        atrasados={[]}
        seleccionados={[]}
        onToggleSeleccion={vi.fn()}
      />,
    )

    expect(screen.getByText(/no hay alumnos atrasados/i)).toBeInTheDocument()
  })

  it('llama a onToggleSeleccion al hacer clic en el checkbox', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()

    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={[]}
        onToggleSeleccion={onToggle}
      />,
    )

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[0])

    expect(onToggle).toHaveBeenCalledWith('ep-1')
  })

  it('muestra botón de comunicar cuando hay seleccionados y se proporciona callback', () => {
    const onComunicar = vi.fn()

    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={['ep-1']}
        onToggleSeleccion={vi.fn()}
        onComunicar={onComunicar}
      />,
    )

    expect(screen.getByText(/comunicar seleccionados/i)).toBeInTheDocument()
  })

  it('no muestra el botón de comunicar cuando no hay seleccionados', () => {
    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={[]}
        onToggleSeleccion={vi.fn()}
        onComunicar={vi.fn()}
      />,
    )

    expect(screen.queryByText(/comunicar seleccionados/i)).not.toBeInTheDocument()
  })

  it('muestra "—" cuando no hay actividades faltantes', () => {
    const atrasadoSinActividades = [{
      entrada_padron_id: 'ep-3',
      nombre: 'Pedro',
      apellidos: 'Sanchez',
      comision: null,
      materia_id: 'mat-1',
      actividades_faltantes: [],
      actividades_reprobadas: [],
    }]

    render(
      <TablaAtrasados
        atrasados={atrasadoSinActividades}
        seleccionados={[]}
        onToggleSeleccion={vi.fn()}
      />,
    )

    // comision is null → shows "—"
    // actividades_faltantes is empty → shows "—"
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThan(0)
  })

  it('muestra texto singular "1 alumno seleccionado" para un alumno', () => {
    render(
      <TablaAtrasados
        atrasados={mockAtrasados}
        seleccionados={['ep-1']}
        onToggleSeleccion={vi.fn()}
        onComunicar={vi.fn()}
      />,
    )

    expect(screen.getByText('1 alumno seleccionado')).toBeInTheDocument()
  })
})
