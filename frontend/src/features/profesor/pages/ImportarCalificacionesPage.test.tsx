/**
 * Tests for ImportarCalificacionesPage.
 * TDD: tests written before implementation.
 *
 * Scenarios:
 * - Muestra el stepper en paso 1 (upload) por defecto
 * - Muestra tabla de actividades después del upload exitoso
 * - Botón de confirmar deshabilitado sin actividades seleccionadas
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../services/comisionesService', () => ({
  comisionesService: {
    previewCalificaciones: vi.fn(),
    importarCalificaciones: vi.fn(),
    getAtrasados: vi.fn(),
    getRanking: vi.fn(),
    getNotasFinales: vi.fn(),
    exportSinCorregir: vi.fn(),
    configurarUmbral: vi.fn(),
  },
}))

import { ImportarCalificacionesPage } from './ImportarCalificacionesPage'

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage() {
  const qc = makeQC()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={['/profesor/comisiones/mat-1/importar']}
      >
        <Routes>
          <Route
            path="/profesor/comisiones/:comisionId/importar"
            element={<ImportarCalificacionesPage />}
          />
          <Route path="/profesor/comisiones/:comisionId" element={<div>Comision Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ImportarCalificacionesPage', () => {
  it('muestra el stepper en el paso 1 "Subir archivo" por defecto', () => {
    renderPage()

    expect(screen.getByText('Subir archivo')).toBeInTheDocument()
    expect(screen.getByText('Seleccionar actividades')).toBeInTheDocument()
    expect(screen.getByText('Confirmar importación')).toBeInTheDocument()

    // El título del paso 1
    expect(screen.getByText(/subir archivo de calificaciones/i)).toBeInTheDocument()
  })

  it('muestra la zona de drag-and-drop en el paso 1', () => {
    renderPage()

    expect(
      screen.getByLabelText(/zona de carga de archivo/i),
    ).toBeInTheDocument()
  })

  it('muestra el título de importación en la página', () => {
    renderPage()

    expect(screen.getByText('Importar Calificaciones')).toBeInTheDocument()
  })

  it('muestra botón de volver', () => {
    renderPage()

    expect(screen.getByText(/← volver/i)).toBeInTheDocument()
  })
})
