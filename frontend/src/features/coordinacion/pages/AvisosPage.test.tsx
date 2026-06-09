/**
 * Tests for AvisosPage.
 *
 * Scenarios:
 * - Renderiza lista de avisos con badges de severidad
 * - Muestra fondo rojo para avisos Críticos
 * - Abre el drawer de publicación
 * - Archivar aviso con confirmación
 * - Estado vacío cuando no hay avisos
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/shared/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

import { api } from '@/shared/services/api'
import { AvisosPage } from './AvisosPage'
import type { Aviso } from '../types/coordinacion.types'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AvisosPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const mockAvisos: Aviso[] = [
  {
    id: 'aviso-1',
    alcance: 'Global',
    materia_id: null,
    cohorte_id: null,
    rol_destino: null,
    severidad: 'Info',
    titulo: 'Aviso informativo',
    cuerpo: 'Contenido del aviso.',
    inicio_en: '2026-06-01T00:00:00Z',
    fin_en: null,
    orden: 0,
    activo: true,
    requiere_ack: false,
  },
  {
    id: 'aviso-2',
    alcance: 'PorRol',
    materia_id: null,
    cohorte_id: null,
    rol_destino: 'PROFESOR',
    severidad: 'Crítico',
    titulo: 'Cierre urgente',
    cuerpo: 'Acción requerida urgente.',
    inicio_en: '2026-06-01T00:00:00Z',
    fin_en: null,
    orden: 1,
    activo: true,
    requiere_ack: true,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AvisosPage', () => {
  it('renderiza lista de avisos con badges de severidad', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockAvisos })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Aviso informativo')).toBeInTheDocument()
      expect(screen.getByText('Cierre urgente')).toBeInTheDocument()
      expect(screen.getByText('Info')).toBeInTheDocument()
      expect(screen.getByText('Crítico')).toBeInTheDocument()
    })
  })

  it('muestra estado vacío cuando no hay avisos activos', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/no hay avisos activos/i)).toBeInTheDocument()
    })
  })

  it('filtra avisos inactivos de la lista', async () => {
    const avisosConInactivo: Aviso[] = [
      ...mockAvisos,
      { ...mockAvisos[0], id: 'aviso-3', titulo: 'Aviso archivado', activo: false },
    ]
    vi.mocked(api.get).mockResolvedValueOnce({ data: avisosConInactivo })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Aviso informativo')).toBeInTheDocument()
    })
    expect(screen.queryByText('Aviso archivado')).not.toBeInTheDocument()
  })

  it('abre el drawer al hacer click en "Publicar aviso"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    const btn = screen.getByRole('button', { name: /publicar aviso/i })
    fireEvent.click(btn)

    expect(screen.getByRole('dialog', { name: /publicar aviso/i })).toBeInTheDocument()
  })

  it('muestra el campo de materia_id cuando se selecciona alcance "Por materia"', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /publicar aviso/i }))

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'PorMateria' } })

    expect(screen.getByPlaceholderText(/uuid de la materia/i)).toBeInTheDocument()
  })
})
