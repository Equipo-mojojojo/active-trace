/**
 * Service for grilla salarial API calls.
 *
 * Endpoints (backend spec grilla-salarial, C-18):
 *  GET  /api/liquidaciones/salarios/base          — List salarios base
 *  POST /api/liquidaciones/salarios/base          — Crear salario base
 *  PUT  /api/liquidaciones/salarios/base/{id}     — Editar salario base
 *  DELETE /api/liquidaciones/salarios/base/{id}   — Eliminar salario base
 *  GET  /api/liquidaciones/salarios/plus          — List salarios plus
 *  POST /api/liquidaciones/salarios/plus          — Crear salario plus
 *  PUT  /api/liquidaciones/salarios/plus/{id}     — Editar salario plus
 *  DELETE /api/liquidaciones/salarios/plus/{id}   — Eliminar salario plus
 */
import { api } from '@/shared/services/api'
import type {
  SalarioBase,
  SalarioBaseCreate,
  SalarioPlus,
  SalarioPlusCreate,
  SalarioPlusFilters,
} from '../types/finanzas.types'

export const grillaSalarialService = {
  // ── Salario Base ────────────────────────────────────────────────────────────
  async getSalariosBase(): Promise<SalarioBase[]> {
    const { data } = await api.get<SalarioBase[]>('/api/liquidaciones/salarios/base')
    return data
  },

  async createSalarioBase(payload: SalarioBaseCreate): Promise<SalarioBase> {
    const { data } = await api.post<SalarioBase>('/api/liquidaciones/salarios/base', payload)
    return data
  },

  async updateSalarioBase(id: string, payload: SalarioBaseCreate): Promise<SalarioBase> {
    const { data } = await api.put<SalarioBase>(
      `/api/liquidaciones/salarios/base/${id}`,
      payload,
    )
    return data
  },

  async deleteSalarioBase(id: string): Promise<void> {
    await api.delete(`/api/liquidaciones/salarios/base/${id}`)
  },

  // ── Salario Plus ────────────────────────────────────────────────────────────
  async getSalariosPlus(filters: SalarioPlusFilters = {}): Promise<SalarioPlus[]> {
    const { data } = await api.get<SalarioPlus[]>('/api/liquidaciones/salarios/plus', {
      params: filters,
    })
    return data
  },

  async createSalarioPlus(payload: SalarioPlusCreate): Promise<SalarioPlus> {
    const { data } = await api.post<SalarioPlus>('/api/liquidaciones/salarios/plus', payload)
    return data
  },

  async updateSalarioPlus(id: string, payload: SalarioPlusCreate): Promise<SalarioPlus> {
    const { data } = await api.put<SalarioPlus>(
      `/api/liquidaciones/salarios/plus/${id}`,
      payload,
    )
    return data
  },

  async deleteSalarioPlus(id: string): Promise<void> {
    await api.delete(`/api/liquidaciones/salarios/plus/${id}`)
  },
}
