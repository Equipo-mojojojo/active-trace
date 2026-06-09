import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { estructuraService } from '../services/estructuraService'
import type {
  CarreraCreate,
  CohorteCreate,
  MateriaCreate,
} from '../types/admin.types'

export const estructuraQueryKeys = {
  carreras: () => ['admin', 'carreras'] as const,
  cohortes: () => ['admin', 'cohortes'] as const,
  materias: () => ['admin', 'materias'] as const,
}

// ── Carreras ──────────────────────────────────────────────────────────────────

export function useCarreras() {
  return useQuery({
    queryKey: estructuraQueryKeys.carreras(),
    queryFn: () => estructuraService.getCarreras(),
  })
}

export function useCreateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CarreraCreate) => estructuraService.createCarrera(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'carreras'] })
    },
  })
}

export function useUpdateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CarreraCreate }) =>
      estructuraService.updateCarrera(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'carreras'] })
    },
  })
}

export function useDeleteCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteCarrera(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'carreras'] })
    },
  })
}

// ── Cohortes ──────────────────────────────────────────────────────────────────

export function useCohortes() {
  return useQuery({
    queryKey: estructuraQueryKeys.cohortes(),
    queryFn: () => estructuraService.getCohortes(),
  })
}

export function useCreateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CohorteCreate) => estructuraService.createCohorte(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cohortes'] })
    },
  })
}

export function useUpdateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CohorteCreate }) =>
      estructuraService.updateCohorte(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cohortes'] })
    },
  })
}

export function useDeleteCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteCohorte(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cohortes'] })
    },
  })
}

// ── Materias ──────────────────────────────────────────────────────────────────

export function useMaterias() {
  return useQuery({
    queryKey: estructuraQueryKeys.materias(),
    queryFn: () => estructuraService.getMaterias(),
  })
}

export function useCreateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: MateriaCreate) => estructuraService.createMateria(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'materias'] })
    },
  })
}

export function useUpdateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MateriaCreate }) =>
      estructuraService.updateMateria(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'materias'] })
    },
  })
}

export function useDeleteMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteMateria(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'materias'] })
    },
  })
}
