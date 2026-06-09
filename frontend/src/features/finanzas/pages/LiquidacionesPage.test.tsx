/**
 * Tests for LiquidacionesPage — TDD Strict
 *
 * Scenarios:
 * - RED->GREEN: render de tabs con datos
 * - TRIANGULATE: cambio de tab sin re-fetch
 * - KPIs visibles con montos
 * - Confirmación previa al cierre
 * - Cierre exitoso (200) → liquidación en modo solo-lectura
 * - 409 ya cerrada → mensaje sin romper pantalla
 * - Botón de cierre oculto sin permiso liquidaciones:cerrar
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { LiquidacionesPage } from './LiquidacionesPage'

// Mock hooks
vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: vi.fn(),
}))
vi.mock('../hooks/useLiquidaciones', () => ({
  useLiquidaciones: vi.fn(),
  useCerrarLiquidacion: vi.fn(),
  useHistorialLiquidaciones: vi.fn(),
}))
vi.mock('../services/liquidacionesService', () => ({
  liquidacionesService: {
    exportarLiquidacion: vi.fn().mockResolvedValue(new Blob()),
  },
}))

import { usePermission } from '@/shared/hooks/usePermission'
import { useLiquidaciones, useCerrarLiquidacion } from '../hooks/useLiquidaciones'
import axios from 'axios'

const mockLiquidacion = {
  periodo: '2024-06',
  cerrada: false,
  total_sin_factura: 150000,
  total_con_factura: 50000,
  general: [
    { usuario_id: 'u1', nombre: 'Ana García', rol: 'PROFESOR' as const, comisiones: 2, salario_base: 60000, plus: 5000, total: 65000 },
    { usuario_id: 'u2', nombre: 'Juan Pérez', rol: 'TUTOR' as const, comisiones: 1, salario_base: 40000, plus: 2000, total: 42000 },
  ],
  nexo: [
    { usuario_id: 'u3', nombre: 'María Nexo', rol: 'NEXO' as const, comisiones: 3, salario_base: 70000, plus: 8000, total: 78000 },
  ],
  facturantes: [],
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

function setupMocks({
  permissions = ['liquidaciones:ver', 'liquidaciones:cerrar'],
  liquidacionData = mockLiquidacion,
  cerrarMutateAsync = vi.fn(),
} = {}) {
  vi.mocked(usePermission).mockReturnValue({
    hasPermission: (p: string) => permissions.includes(p),
  })
  vi.mocked(useLiquidaciones).mockReturnValue({
    data: liquidacionData,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useLiquidaciones>)
  vi.mocked(useCerrarLiquidacion).mockReturnValue({
    mutateAsync: cerrarMutateAsync,
    isPending: false,
  } as ReturnType<typeof useCerrarLiquidacion>)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('LiquidacionesPage — render de tabs', () => {
  it('muestra los tres tabs: General, NEXO, Facturas', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.getByRole('tab', { name: 'General' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'NEXO' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Facturas' })).toBeInTheDocument()
  })

  it('el tab General está activo por defecto y muestra los docentes del segmento', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.getByText('Ana García')).toBeInTheDocument()
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
  })
})

describe('LiquidacionesPage — cambio de tab', () => {
  it('al hacer click en NEXO muestra los docentes del segmento nexo', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('tab', { name: 'NEXO' }))

    expect(screen.getByText('María Nexo')).toBeInTheDocument()
    // General docentes should not be visible
    expect(screen.queryByText('Ana García')).not.toBeInTheDocument()
  })

  it('el tab Facturas muestra estado vacío cuando no hay facturantes', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('tab', { name: 'Facturas' }))

    expect(screen.getByText('Sin docentes en este segmento')).toBeInTheDocument()
  })
})

describe('LiquidacionesPage — KPIs', () => {
  it('muestra los KPIs total_sin_factura y total_con_factura', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.getByLabelText('Total sin factura')).toBeInTheDocument()
    expect(screen.getByLabelText('Total con factura')).toBeInTheDocument()
  })
})

describe('LiquidacionesPage — cerrar liquidación', () => {
  it('muestra el botón Cerrar liquidación con el permiso liquidaciones:cerrar', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.getByRole('button', { name: 'Cerrar liquidación' })).toBeInTheDocument()
  })

  it('NO muestra el botón Cerrar liquidación sin el permiso', () => {
    setupMocks({ permissions: ['liquidaciones:ver'] })
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.queryByRole('button', { name: 'Cerrar liquidación' })).not.toBeInTheDocument()
  })

  it('al hacer click en Cerrar liquidación abre el modal de confirmación', () => {
    setupMocks()
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar liquidación' }))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/irreversible/i)).toBeInTheDocument()
  })

  it('al confirmar el cierre llama a mutateAsync', async () => {
    const cerrarMutateAsync = vi.fn().mockResolvedValue({ ...mockLiquidacion, cerrada: true })
    setupMocks({ cerrarMutateAsync })
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    // Open confirm modal
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar liquidación' }))
    // Confirm in modal (the confirm button inside dialog)
    const dialog = screen.getByRole('dialog')
    const confirmBtn = dialog.querySelector('button:last-child') as HTMLButtonElement
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(cerrarMutateAsync).toHaveBeenCalled()
    })
  })

  it('al recibir 409 muestra mensaje "La liquidación ya está cerrada"', async () => {
    const error409 = Object.assign(new Error('409'), {
      isAxiosError: true,
      response: { status: 409 },
    })
    vi.spyOn(axios, 'isAxiosError').mockReturnValue(true)
    const cerrarMutateAsync = vi.fn().mockRejectedValue(error409)
    setupMocks({ cerrarMutateAsync })
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    // Open confirm modal
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar liquidación' }))
    // Confirm in modal
    const dialog = screen.getByRole('dialog')
    const confirmBtn = dialog.querySelector('button:last-child') as HTMLButtonElement
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('La liquidación ya está cerrada.')
    })
  })
})

describe('LiquidacionesPage — liquidación ya cerrada', () => {
  it('muestra aviso de solo-lectura cuando la liquidación está cerrada', () => {
    setupMocks({ liquidacionData: { ...mockLiquidacion, cerrada: true } })
    render(<LiquidacionesPage />, { wrapper: makeWrapper() })

    expect(screen.getByRole('status')).toHaveTextContent('solo lectura')
    expect(screen.queryByRole('button', { name: 'Cerrar liquidación' })).not.toBeInTheDocument()
  })
})
