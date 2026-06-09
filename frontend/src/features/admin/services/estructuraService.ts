/**
 * Service for estructura académica API calls.
 *
 * Endpoints (backend specs estructura-carreras, estructura-cohortes, estructura-materias, C-06/C-07):
 *  GET    /api/admin/carreras            — List carreras
 *  POST   /api/admin/carreras            — Crear carrera
 *  PUT    /api/admin/carreras/{id}       — Editar carrera
 *  DELETE /api/admin/carreras/{id}       — Soft delete carrera
 *  GET    /api/admin/cohortes            — List cohortes
 *  POST   /api/admin/cohortes            — Crear cohorte
 *  PUT    /api/admin/cohortes/{id}       — Editar cohorte
 *  DELETE /api/admin/cohortes/{id}       — Soft delete cohorte
 *  GET    /api/admin/materias            — List materias
 *  POST   /api/admin/materias            — Crear materia
 *  PUT    /api/admin/materias/{id}       — Editar materia
 *  DELETE /api/admin/materias/{id}       — Soft delete materia
 */
import { api } from '@/shared/services/api'
import type {
  Carrera,
  CarreraCreate,
  Cohorte,
  CohorteCreate,
  Materia,
  MateriaCreate,
} from '../types/admin.types'

export const estructuraService = {
  // ── Carreras ────────────────────────────────────────────────────────────────
  async getCarreras(): Promise<Carrera[]> {
    const { data } = await api.get<Carrera[]>('/api/admin/carreras')
    return data
  },

  async createCarrera(payload: CarreraCreate): Promise<Carrera> {
    const { data } = await api.post<Carrera>('/api/admin/carreras', payload)
    return data
  },

  async updateCarrera(id: string, payload: CarreraCreate): Promise<Carrera> {
    const { data } = await api.put<Carrera>(`/api/admin/carreras/${id}`, payload)
    return data
  },

  async deleteCarrera(id: string): Promise<void> {
    await api.delete(`/api/admin/carreras/${id}`)
  },

  // ── Cohortes ────────────────────────────────────────────────────────────────
  async getCohortes(): Promise<Cohorte[]> {
    const { data } = await api.get<Cohorte[]>('/api/admin/cohortes')
    return data
  },

  async createCohorte(payload: CohorteCreate): Promise<Cohorte> {
    const { data } = await api.post<Cohorte>('/api/admin/cohortes', payload)
    return data
  },

  async updateCohorte(id: string, payload: CohorteCreate): Promise<Cohorte> {
    const { data } = await api.put<Cohorte>(`/api/admin/cohortes/${id}`, payload)
    return data
  },

  async deleteCohorte(id: string): Promise<void> {
    await api.delete(`/api/admin/cohortes/${id}`)
  },

  // ── Materias ────────────────────────────────────────────────────────────────
  async getMaterias(): Promise<Materia[]> {
    const { data } = await api.get<Materia[]>('/api/admin/materias')
    return data
  },

  async createMateria(payload: MateriaCreate): Promise<Materia> {
    const { data } = await api.post<Materia>('/api/admin/materias', payload)
    return data
  },

  async updateMateria(id: string, payload: MateriaCreate): Promise<Materia> {
    const { data } = await api.put<Materia>(`/api/admin/materias/${id}`, payload)
    return data
  },

  async deleteMateria(id: string): Promise<void> {
    await api.delete(`/api/admin/materias/${id}`)
  },
}
