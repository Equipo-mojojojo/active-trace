import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { equiposService } from '../services/equiposService'
import type {
  Asignacion,
  AsignacionCreate,
  AsignacionMasivaRequest,
  ClonarEquipoRequest,
  EquiposFilters,
} from '../types/coordinacion.types'

export const queryKeys = {
  equipos: (filters: EquiposFilters) => ['equipos', filters] as const,
}

export function useEquipos(filters: EquiposFilters = {}) {
  return useQuery<Asignacion[]>({
    queryKey: queryKeys.equipos(filters),
    queryFn: () => equiposService.getEquipos(filters),
  })
}

export function useCreateAsignacion() {
  const queryClient = useQueryClient()
  return useMutation<Asignacion, Error, AsignacionCreate>({
    mutationFn: (payload) => equiposService.createAsignacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useUpdateAsignacion() {
  const queryClient = useQueryClient()
  return useMutation<Asignacion, Error, { id: string; payload: Partial<AsignacionCreate> }>({
    mutationFn: ({ id, payload }) => equiposService.updateAsignacion(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useDeleteAsignacion() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => equiposService.deleteAsignacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AsignacionMasivaRequest) => equiposService.asignacionMasiva(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useClonarEquipo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClonarEquipoRequest) => equiposService.clonarEquipo(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}
