/**
 * Tests for ComunicacionPage.
 * TDD: tests written before/alongside implementation.
 *
 * Scenarios:
 * - Botón enviar deshabilitado cuando no hay destinatarios seleccionados
 * - Muestra validación inline cuando no hay destinatarios
 * - Llama al service al enviar con destinatarios seleccionados
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../services/comunicacionesService', () => ({
  comunicacionesService: {
    getPreviewMensaje: vi.fn(),
    enviarComunicacion: vi.fn(),
    getLote: vi.fn(),
  },
}))

import { comunicacionesService } from '../services/comunicacionesService'
import { ComunicacionPage } from './ComunicacionPage'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage(initialState?: object) {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={[
          { pathname: '/profesor/comunicacion/mat-1', state: initialState },
        ]}
      >
        <Routes>
          <Route path="/profesor/comunicacion/:comisionId" element={<ComunicacionPage />} />
          <Route path="/profesor/comunicacion/tracking" element={<div>Tracking Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ComunicacionPage', () => {
  it('muestra botón deshabilitado sin destinatarios', () => {
    renderPage()

    const btn = screen.getByRole('button', { name: /seleccioná al menos/i })
    expect(btn).toBeDisabled()
  })

  it('muestra mensaje informativo cuando no hay destinatarios seleccionados', () => {
    renderPage()

    expect(
      screen.getByText(/seleccioná al menos un destinatario/i),
    ).toBeInTheDocument()
  })

  it('llama al service de preview cuando hay destinatarios en el state inicial', async () => {
    const mockPreview = {
      requiere_aprobacion: false,
      preview: [
        {
          entrada_padron_id: 'ep-1',
          destinatario_nombre: 'Juan Perez',
          destinatario_email: 'juan@example.com',
          asunto: 'Aviso',
          cuerpo: 'Cuerpo del mensaje',
        },
      ],
    }
    vi.mocked(comunicacionesService.getPreviewMensaje).mockResolvedValue(mockPreview)

    renderPage({ destinatariosIds: ['ep-1'] })

    await waitFor(() => {
      expect(comunicacionesService.getPreviewMensaje).toHaveBeenCalled()
    })
  })

  it('llama a enviarComunicacion cuando el botón es clickeado con destinatarios', async () => {
    const user = userEvent.setup()
    const mockPreview = {
      requiere_aprobacion: false,
      preview: [
        {
          entrada_padron_id: 'ep-1',
          destinatario_nombre: 'Juan Perez',
          destinatario_email: 'juan@example.com',
          asunto: 'Aviso',
          cuerpo: 'Cuerpo',
        },
      ],
    }
    vi.mocked(comunicacionesService.getPreviewMensaje).mockResolvedValue(mockPreview)
    vi.mocked(comunicacionesService.enviarComunicacion).mockResolvedValueOnce({
      lote_id: 'lote-1',
      total: 1,
      requiere_aprobacion: false,
      comunicaciones: [],
    })

    renderPage({ destinatariosIds: ['ep-1'] })

    await waitFor(() => {
      expect(comunicacionesService.getPreviewMensaje).toHaveBeenCalled()
    })

    // Find the send button — it uses a dynamic aria-label based on count
    // Look for any enabled send button
    await waitFor(() => {
      const btns = screen.getAllByRole('button')
      const sendBtn = btns.find((b) => !b.disabled && b.textContent?.includes('Enviar'))
      expect(sendBtn).toBeInTheDocument()
    })

    const btns = screen.getAllByRole('button')
    const sendBtn = btns.find((b) => !b.disabled && b.textContent?.includes('Enviar'))!
    await user.click(sendBtn)

    await waitFor(() => {
      expect(comunicacionesService.enviarComunicacion).toHaveBeenCalled()
    })
  })
})
