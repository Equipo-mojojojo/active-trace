/**
 * Service for facturas API calls.
 *
 * Endpoints (backend spec factura-docente, C-18):
 *  GET   /api/facturas/               — List facturas con filtros
 *  POST  /api/facturas/               — Crear factura
 *  PATCH /api/facturas/{id}/estado    — Cambiar estado (pendiente↔abonada)
 *  PUT   /api/facturas/{id}/archivo   — Adjuntar archivo (multipart/FormData)
 */
import { api } from '@/shared/services/api'
import type {
  Factura,
  FacturaCreate,
  FacturaFilters,
  EstadoFactura,
} from '../types/finanzas.types'

export const facturasService = {
  async getFacturas(filters: FacturaFilters = {}): Promise<Factura[]> {
    const { data } = await api.get<Factura[]>('/api/facturas/', { params: filters })
    return data
  },

  async crearFactura(payload: FacturaCreate): Promise<Factura> {
    const { data } = await api.post<Factura>('/api/facturas/', payload)
    return data
  },

  async cambiarEstado(id: string, estado: EstadoFactura): Promise<Factura> {
    const { data } = await api.patch<Factura>(`/api/facturas/${id}/estado`, { estado })
    return data
  },

  async adjuntarArchivo(id: string, file: File): Promise<Factura> {
    const formData = new FormData()
    formData.append('archivo', file)
    const { data } = await api.put<Factura>(`/api/facturas/${id}/archivo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
