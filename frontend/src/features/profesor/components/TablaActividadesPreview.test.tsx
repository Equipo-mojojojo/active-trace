/**
 * Tests for TablaActividadesPreview.
 * TDD: tests written alongside implementation.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TablaActividadesPreview } from './TablaActividadesPreview'
import type { ActividadDetectada } from '../types/profesor.types'

const mockActividades: ActividadDetectada[] = [
  { nombre: 'TP1', tipo: 'numerica', muestra_valores: ['8', '9', '10'] },
  { nombre: 'TP2', tipo: 'textual', muestra_valores: ['Sí', 'No'] },
  { nombre: 'Parcial', tipo: 'numerica', muestra_valores: ['7', '8'] },
]

describe('TablaActividadesPreview', () => {
  it('renderiza todas las actividades detectadas', () => {
    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={['TP1', 'TP2', 'Parcial']}
        onToggle={vi.fn()}
      />,
    )

    expect(screen.getByText('TP1')).toBeInTheDocument()
    expect(screen.getByText('TP2')).toBeInTheDocument()
    expect(screen.getByText('Parcial')).toBeInTheDocument()
  })

  it('muestra badge "Numérica" para actividades numéricas', () => {
    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={[]}
        onToggle={vi.fn()}
      />,
    )

    const numericBadges = screen.getAllByText('Numérica')
    expect(numericBadges).toHaveLength(2)
    expect(screen.getByText('Texto')).toBeInTheDocument()
  })

  it('llama a onToggle con el nombre de la actividad al hacer clic', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()

    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={[]}
        onToggle={onToggle}
      />,
    )

    const checkboxes = screen.getAllByRole('checkbox')
    // First checkbox is "select all", second is TP1
    await user.click(checkboxes[1])

    expect(onToggle).toHaveBeenCalledWith('TP1')
  })

  it('checkbox de "seleccionar todos" aparece marcado cuando todos están seleccionados', () => {
    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={['TP1', 'TP2', 'Parcial']}
        onToggle={vi.fn()}
      />,
    )

    const checkboxes = screen.getAllByRole('checkbox')
    const toggleAllCheckbox = checkboxes[0]
    expect(toggleAllCheckbox).toBeChecked()
  })

  it('muestra valores de muestra truncados a 3', () => {
    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={[]}
        onToggle={vi.fn()}
      />,
    )

    // TP1 has values: 8, 9, 10 → shown as "8, 9, 10"
    expect(screen.getByText('8, 9, 10')).toBeInTheDocument()
  })

  it('el toggle-all deselecciona todo cuando todas están seleccionadas', async () => {
    const user = userEvent.setup()
    const toggleCalls: string[] = []
    const onToggle = (nombre: string) => toggleCalls.push(nombre)

    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={['TP1', 'TP2', 'Parcial']}
        onToggle={onToggle}
      />,
    )

    const toggleAllCheckbox = screen.getAllByRole('checkbox')[0]
    // All are selected → clicking toggle-all should deselect all
    await user.click(toggleAllCheckbox)

    // Should call onToggle for each selected item
    expect(toggleCalls).toContain('TP1')
    expect(toggleCalls).toContain('TP2')
    expect(toggleCalls).toContain('Parcial')
  })

  it('el toggle-all selecciona todo cuando ninguna está seleccionada', async () => {
    const user = userEvent.setup()
    const toggleCalls: string[] = []
    const onToggle = (nombre: string) => toggleCalls.push(nombre)

    render(
      <TablaActividadesPreview
        actividades={mockActividades}
        seleccionadas={[]}
        onToggle={onToggle}
      />,
    )

    const toggleAllCheckbox = screen.getAllByRole('checkbox')[0]
    await user.click(toggleAllCheckbox)

    expect(toggleCalls).toContain('TP1')
    expect(toggleCalls).toContain('TP2')
    expect(toggleCalls).toContain('Parcial')
  })
})
