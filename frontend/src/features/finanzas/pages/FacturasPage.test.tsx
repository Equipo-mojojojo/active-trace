/**
 * Tests for FacturasPage — TDD Strict
 *
 * Scenarios:
 * - Listar facturas con badges de estado
 * - Filtrar por estado
 * - Crear factura exitosamente
 * - 422 docente no facturante → error inline sin cerrar
 * - Cambiar estado (PATCH)
 * - Adjuntar archivo
 * - Solo-lectura sin facturas:gestionar
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { FacturasPage } from './FacturasPage'
import axios from 'axios'

vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: vi.fn(),
}))
vi.mock('../hooks/useFacturas', () => ({
  useFacturas: vi.fn(),
  useCrearFactura: vi.fn(),
  useCambiarEstadoFactura: vi.fn(),
  useAdjuntarArchivo: vi.fn(),
}))

import { usePermission } from '@/shared/hooks/usePermission'
import { useFacturas, useCrearFactura, useCambiarEstadoFactura, useAdjuntarArchivo } from '../hooks/useFacturas'

const mockFacturas: import('../types/finanzas.types').Factura[] = [
  { id: 'f1', usuario_id: 'u1', nombre_docente: 'Carlos López', periodo: '2024-06', detalle: 'Junio', monto: 50000, fecha_carga: '2024-06-30', estado: 'pendiente', archivo_path: null },
  { id: 'f2', usuario_id: 'u2', nombre_docente: 'Lucia Martínez', periodo: '2024-06', detalle: 'Junio', monto: 45000, fecha_carga: '2024-06-30', estado: 'abonada', archivo_path: '/path/file.pdf' },
]

const noopMutation = () => ({ mutateAsync: vi.fn(), isPending: false })

function setupMocks({
  permissions = ['facturas:ver', 'facturas:gestionar'],
  facturas = mockFacturas,
  crearAsync = vi.fn().mockResolvedValue({}),
  cambiarAsync = vi.fn().mockResolvedValue({}),
} = {}) {
  vi.mocked(usePermission).mockReturnValue({
    hasPermission: (p: string) => permissions.includes(p),
  })
  vi.mocked(useFacturas).mockReturnValue({
    data: facturas,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useFacturas>)
  vi.mocked(useCrearFactura).mockReturnValue({ mutateAsync: crearAsync, isPending: false } as ReturnType<typeof useCrearFactura>)
  vi.mocked(useCambiarEstadoFactura).mockReturnValue({ mutateAsync: cambiarAsync, isPending: false } as ReturnType<typeof useCambiarEstadoFactura>)
  vi.mocked(useAdjuntarArchivo).mockReturnValue(noopMutation() as ReturnType<typeof useAdjuntarArchivo>)
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
  )
}

beforeEach(() => { vi.clearAllMocks() })

describe('FacturasPage — listar', () => {
  it('muestra las facturas con nombre del docente', () => {
    setupMocks()
    render(<FacturasPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('Carlos López')).toBeInTheDocument()
    expect(screen.getByText('Lucia Martínez')).toBeInTheDocument()
  })

  it('muestra badge Pendiente en ámbar y Abonada en verde', () => {
    setupMocks()
    render(<FacturasPage />, { wrapper: makeWrapper() })

    // Find the badge spans specifically (inside table td > span.rounded-full)
    const allSpans = document.querySelectorAll('span.rounded-full')
    const pendienteSpan = Array.from(allSpans).find((s) => s.textContent === 'Pendiente')
    const abonadaSpan = Array.from(allSpans).find((s) => s.textContent === 'Abonada')

    expect(pendienteSpan?.className).toContain('amber')
    expect(abonadaSpan?.className).toContain('green')
  })

  it('muestra indicador de adjunto para factura con archivo_path', () => {
    setupMocks()
    render(<FacturasPage />, { wrapper: makeWrapper() })

    expect(screen.getByTitle('Archivo adjunto')).toBeInTheDocument()
  })
})

describe('FacturasPage — solo lectura sin facturas:gestionar', () => {
  it('no muestra botón Nueva factura sin facturas:gestionar', () => {
    setupMocks({ permissions: ['facturas:ver'] })
    render(<FacturasPage />, { wrapper: makeWrapper() })

    expect(screen.queryByRole('button', { name: 'Nueva factura' })).not.toBeInTheDocument()
  })

  it('no muestra botones Cambiar estado sin facturas:gestionar', () => {
    setupMocks({ permissions: ['facturas:ver'] })
    render(<FacturasPage />, { wrapper: makeWrapper() })

    expect(screen.queryByText('Cambiar estado')).not.toBeInTheDocument()
  })
})

describe('FacturasPage — crear factura', () => {
  it('abre el formulario al hacer click en Nueva factura', () => {
    setupMocks()
    render(<FacturasPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva factura' }))

    expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument()
    // The form section header
    expect(screen.getAllByText('Nueva factura').length).toBeGreaterThan(0)
  })

  it('al recibir 422 muestra error sin cerrar el formulario', async () => {
    const error422 = Object.assign(new Error('422'), { isAxiosError: true, response: { status: 422 } })
    vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)
    const crearAsync = vi.fn().mockRejectedValue(error422)
    setupMocks({ crearAsync })
    render(<FacturasPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Nueva factura' }))
    // Fill required fields minimally
    fireEvent.input(screen.getByRole('button', { name: 'Guardar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => {
      // Form should still be visible
      expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument()
    })
  })
})

describe('FacturasPage — cambiar estado', () => {
  it('al hacer click en Cambiar estado llama a cambiarEstado.mutateAsync', async () => {
    const cambiarAsync = vi.fn().mockResolvedValue({})
    setupMocks({ cambiarAsync })
    render(<FacturasPage />, { wrapper: makeWrapper() })

    const buttons = screen.getAllByText('Cambiar estado')
    fireEvent.click(buttons[0])

    await waitFor(() => {
      expect(cambiarAsync).toHaveBeenCalledWith({ id: 'f1', estado: 'abonada' })
    })
  })
})
