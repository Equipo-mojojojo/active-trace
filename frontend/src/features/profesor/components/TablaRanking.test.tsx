import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TablaRanking } from './TablaRanking'
import type { RankingEntry } from '../types/profesor.types'

const mockRanking: RankingEntry[] = [
  { entrada_padron_id: 'ep-1', nombre: 'Ana', apellidos: 'Lopez', comision: 'A', aprobadas: 8 },
  { entrada_padron_id: 'ep-2', nombre: 'Juan', apellidos: 'Perez', comision: 'A', aprobadas: 5 },
]

describe('TablaRanking', () => {
  it('renderiza la tabla con datos de ranking', () => {
    render(<TablaRanking ranking={mockRanking} />)

    expect(screen.getByText('Lopez, Ana')).toBeInTheDocument()
    expect(screen.getByText('Perez, Juan')).toBeInTheDocument()
    // Position numbers
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    // Aprobadas badges
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay datos de ranking', () => {
    render(<TablaRanking ranking={[]} />)

    expect(screen.getByText(/no hay datos de ranking/i)).toBeInTheDocument()
  })

  it('muestra comisión de cada alumno', () => {
    render(<TablaRanking ranking={mockRanking} />)

    const comisiones = screen.getAllByText('A')
    expect(comisiones.length).toBeGreaterThan(0)
  })

  it('muestra "—" cuando la comisión es null', () => {
    const rankingWithNull: RankingEntry[] = [
      { entrada_padron_id: 'ep-3', nombre: 'Carlos', apellidos: 'Garcia', comision: null, aprobadas: 3 },
    ]
    render(<TablaRanking ranking={rankingWithNull} />)

    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
