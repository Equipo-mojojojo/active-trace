import { useQuery } from '@tanstack/react-query'
import { auditoriaService } from '../services/auditoriaService'
import type { AuditoriaFilters } from '../types/admin.types'

// actor_id is NEVER sent from the frontend — backend restricts scope from JWT
type AuditoriaQueryFilters = Omit<AuditoriaFilters, 'actor_id'>

export const auditoriaQueryKeys = {
  accionesPorDia: (filters: AuditoriaQueryFilters) =>
    ['auditoria', 'acciones-por-dia', filters] as const,
  estadoComunicaciones: (filters: AuditoriaQueryFilters) =>
    ['auditoria', 'estado-comunicaciones', filters] as const,
  interacciones: (filters: AuditoriaQueryFilters) =>
    ['auditoria', 'interacciones', filters] as const,
  ultimasAcciones: (filters: AuditoriaQueryFilters, limit: number) =>
    ['auditoria', 'ultimas-acciones', filters, limit] as const,
}

export function useAccionesPorDia(filters: AuditoriaQueryFilters = {}) {
  return useQuery({
    queryKey: auditoriaQueryKeys.accionesPorDia(filters),
    queryFn: () => auditoriaService.accionesPorDia(filters),
  })
}

export function useEstadoComunicaciones(filters: AuditoriaQueryFilters = {}) {
  return useQuery({
    queryKey: auditoriaQueryKeys.estadoComunicaciones(filters),
    queryFn: () => auditoriaService.estadoComunicaciones(filters),
  })
}

export function useInteracciones(filters: AuditoriaQueryFilters = {}) {
  return useQuery({
    queryKey: auditoriaQueryKeys.interacciones(filters),
    queryFn: () => auditoriaService.interacciones(filters),
  })
}

export function useUltimasAcciones(filters: AuditoriaQueryFilters = {}, limit = 200) {
  return useQuery({
    queryKey: auditoriaQueryKeys.ultimasAcciones(filters, limit),
    queryFn: () => auditoriaService.ultimasAcciones(filters, limit),
  })
}
