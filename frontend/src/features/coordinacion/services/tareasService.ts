/**
 * Service for tareas internas API calls.
 *
 * Endpoints (backend/app/api/v1/routers/tareas.py):
 *  GET  /api/v1/tareas/mias                          — Mis tareas (asignadas a mí)
 *  GET  /api/v1/tareas                               — Todas las tareas (COORDINADOR)
 *  POST /api/v1/tareas                               — Crear tarea
 *  GET  /api/v1/tareas/{id}                          — Detalle de tarea
 *  PATCH /api/v1/tareas/{id}                         — Actualizar tarea (estado)
 *  GET  /api/v1/tareas/{id}/comentarios              — Comentarios de la tarea
 *  POST /api/v1/tareas/{id}/comentarios              — Agregar comentario
 */
import { api } from '@/shared/services/api'
import type { Tarea, TareaCreate, ComentarioTarea, ComentarioCreate } from '../types/coordinacion.types'

export type TareaTab = 'mias' | 'asignadas' | 'todas'

export const tareasService = {
  async getTareas(tab: TareaTab): Promise<Tarea[]> {
    if (tab === 'mias') {
      const { data } = await api.get<Tarea[]>('/tareas/mias')
      return data
    }
    // 'asignadas' and 'todas' use the same endpoint with different filter handled server-side
    const { data } = await api.get<Tarea[]>('/tareas', {
      params: tab === 'asignadas' ? { asignadas_por_mi: true } : {},
    })
    return data
  },

  async getTarea(id: string): Promise<Tarea> {
    const { data } = await api.get<Tarea>(`/tareas/${id}`)
    return data
  },

  async createTarea(payload: TareaCreate): Promise<Tarea> {
    const { data } = await api.post<Tarea>('/tareas', payload)
    return data
  },

  async updateEstadoTarea(id: string, estado: string): Promise<Tarea> {
    const { data } = await api.patch<Tarea>(`/tareas/${id}`, { estado })
    return data
  },

  async getComentarios(tareaId: string): Promise<ComentarioTarea[]> {
    const { data } = await api.get<ComentarioTarea[]>(`/tareas/${tareaId}/comentarios`)
    return data
  },

  async addComentario(tareaId: string, texto: string): Promise<ComentarioTarea> {
    const payload: ComentarioCreate = { texto }
    const { data } = await api.post<ComentarioTarea>(
      `/tareas/${tareaId}/comentarios`,
      payload,
    )
    return data
  },
}
