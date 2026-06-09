import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrackingTable } from './TrackingTable'
import type { ComunicacionEstado } from '../types/profesor.types'

const mockComunicaciones: ComunicacionEstado[] = [
  {
    id: 'c-1',
    lote_id: 'lote-1',
    entrada_padron_id: 'ep-1',
    destinatario_nombre: 'Juan Perez',
    estado: 'OK',
    requiere_aprobacion: false,
    aprobada: true,
    error_detalle: null,
  },
  {
    id: 'c-2',
    lote_id: 'lote-1',
    entrada_padron_id: 'ep-2',
    destinatario_nombre: 'Ana Lopez',
    estado: 'FALLIDO',
    requiere_aprobacion: false,
    aprobada: false,
    error_detalle: 'Mailbox full',
  },
  {
    id: 'c-3',
    lote_id: 'lote-1',
    entrada_padron_id: 'ep-3',
    destinatario_nombre: 'Carlos Garcia',
    estado: 'PENDIENTE',
    requiere_aprobacion: false,
    aprobada: false,
    error_detalle: null,
  },
]

describe('TrackingTable', () => {
  it('renderiza todas las comunicaciones cuando no hay filtro', () => {
    render(<TrackingTable comunicaciones={mockComunicaciones} filtroEstado="" />)

    expect(screen.getByText('Juan Perez')).toBeInTheDocument()
    expect(screen.getByText('Ana Lopez')).toBeInTheDocument()
    expect(screen.getByText('Carlos Garcia')).toBeInTheDocument()
  })

  it('filtra comunicaciones por estado', () => {
    render(<TrackingTable comunicaciones={mockComunicaciones} filtroEstado="FALLIDO" />)

    expect(screen.queryByText('Juan Perez')).not.toBeInTheDocument()
    expect(screen.getByText('Ana Lopez')).toBeInTheDocument()
  })

  it('muestra badge verde para estado OK', () => {
    render(<TrackingTable comunicaciones={[mockComunicaciones[0]]} filtroEstado="" />)

    expect(screen.getByText('Enviado')).toBeInTheDocument()
  })

  it('muestra badge rojo para estado FALLIDO', () => {
    render(<TrackingTable comunicaciones={[mockComunicaciones[1]]} filtroEstado="" />)

    expect(screen.getByText('Fallido')).toBeInTheDocument()
  })

  it('muestra badge amarillo para estado PENDIENTE', () => {
    render(<TrackingTable comunicaciones={[mockComunicaciones[2]]} filtroEstado="" />)

    expect(screen.getByText('Pendiente')).toBeInTheDocument()
  })

  it('muestra mensaje de estado vacío cuando no hay comunicaciones', () => {
    render(<TrackingTable comunicaciones={[]} filtroEstado="" />)

    expect(screen.getByText(/no hay comunicaciones/i)).toBeInTheDocument()
  })

  it('muestra "No hay comunicaciones con ese estado" cuando el filtro no tiene resultados', () => {
    render(<TrackingTable comunicaciones={mockComunicaciones} filtroEstado="CANCELADO" />)

    expect(screen.getByText(/no hay comunicaciones con ese estado/i)).toBeInTheDocument()
  })

  it('muestra error_detalle cuando está disponible', () => {
    render(<TrackingTable comunicaciones={[mockComunicaciones[1]]} filtroEstado="" />)

    expect(screen.getByText('Mailbox full')).toBeInTheDocument()
  })

  it('muestra "—" cuando no hay error_detalle', () => {
    render(<TrackingTable comunicaciones={[mockComunicaciones[0]]} filtroEstado="" />)

    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
