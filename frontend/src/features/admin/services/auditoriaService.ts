/**
 * Service for auditoria metrics API calls.
 *
 * Endpoints (backend spec metricas-panel-auditoria, C-19):
 *  GET /api/v1/auditoria/metricas/acciones-por-dia      — Serie temporal de acciones
 *  GET /api/v1/auditoria/metricas/estado-comunicaciones — Estado por docente
 *  GET /api/v1/auditoria/metricas/interacciones         — Interacciones por docente x materia
 *  GET /api/v1/auditoria/metricas/ultimas-acciones      — Log completo (cap 200)
 *
 * CRITICAL: The frontend NEVER sends actor_id for own-scope restriction.
 * When a COORDINADOR has auditoria:ver:propio, the backend restricts scope
 * automatically from the JWT session. The UI sends no actor_id parameter.
 */
import { api } from '@/shared/services/api'
import type {
  AuditoriaFilters,
  AccionPorDia,
  EstadoComunicacionDocente,
  InteraccionDocente,
  UltimaAccion,
} from '../types/admin.types'

export const auditoriaService = {
  async accionesPorDia(filters: Omit<AuditoriaFilters, 'actor_id'> = {}): Promise<AccionPorDia[]> {
    const { data } = await api.get<AccionPorDia[]>(
      '/auditoria/metricas/acciones-por-dia',
      { params: filters },
    )
    return data
  },

  async estadoComunicaciones(
    filters: Omit<AuditoriaFilters, 'actor_id'> = {},
  ): Promise<EstadoComunicacionDocente[]> {
    const { data } = await api.get<EstadoComunicacionDocente[]>(
      '/auditoria/metricas/estado-comunicaciones',
      { params: filters },
    )
    return data
  },

  async interacciones(
    filters: Omit<AuditoriaFilters, 'actor_id'> = {},
  ): Promise<InteraccionDocente[]> {
    const { data } = await api.get<InteraccionDocente[]>(
      '/auditoria/metricas/interacciones',
      { params: filters },
    )
    return data
  },

  async ultimasAcciones(
    filters: Omit<AuditoriaFilters, 'actor_id'> = {},
    limit = 200,
  ): Promise<UltimaAccion[]> {
    const { data } = await api.get<UltimaAccion[]>(
      '/auditoria/metricas/ultimas-acciones',
      { params: { ...filters, limit } },
    )
    return data
  },
}
