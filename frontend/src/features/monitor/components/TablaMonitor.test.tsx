import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TablaMonitor } from './TablaMonitor'
import type { MonitorEntry } from '@/features/profesor/types/profesor.types'

const mockEntries: MonitorEntry[] = [
  {
    entrada_padron_id: 'ep-1',
    nombre: 'Juan',
    apellidos: 'Perez',
    comision: 'A',
    regional: null,
    materia_id: 'mat-1',
    aprobadas: 5,
    reprobadas: 2,
    faltantes: 1,
    atrasado: true,
  },
  {
    entrada_padron_id: 'ep-2',
    nombre: 'Ana',
    apellidos: 'Lopez',
    comision: null,
    regional: null,
    materia_id: 'mat-1',
    aprobadas: 8,
    reprobadas: 0,
    faltantes: 0,
    atrasado: false,
  },
]

describe('TablaMonitor', () => {
  it('renderiza entradas de alumnos con sus datos', () => {
    render(<TablaMonitor entries={mockEntries} />)

    expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    expect(screen.getByText('Lopez, Ana')).toBeInTheDocument()
  })

  it('muestra badge "Atrasado" y "Al día" según el estado', () => {
    render(<TablaMonitor entries={mockEntries} />)

    expect(screen.getByText('Atrasado')).toBeInTheDocument()
    expect(screen.getByText('Al día')).toBeInTheDocument()
  })

  it('muestra "—" cuando comision es null', () => {
    render(<TablaMonitor entries={mockEntries} />)

    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay entradas', () => {
    render(<TablaMonitor entries={[]} />)

    expect(screen.getByText(/no se encontraron alumnos/i)).toBeInTheDocument()
  })

  it('calcula correctamente el porcentaje de aprobadas', () => {
    render(<TablaMonitor entries={[mockEntries[0]]} />)

    // Juan: 5 aprobadas / (5+2+1) = 62.5% → rounds to 63%
    // Text is split across elements, use getAllByText or contains check
    const cell = screen.getByText(/63%/)
    expect(cell).toBeInTheDocument()
  })
})
