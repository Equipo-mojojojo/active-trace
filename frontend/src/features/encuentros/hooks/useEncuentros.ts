import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { encuentrosService } from '../services/encuentrosService'
import type {
  SlotEncuentro,
  SlotEncuentroCreate,
  InstanciaEncuentro,
  InstanciaEncuentroUpdate,
  EncuentrosFilters,
} from '../types/encuentros.types'

export const encuentroQueryKeys = {
  encuentros: (filters: EncuentrosFilters) => ['encuentros', filters] as const,
  instancias: (filters: EncuentrosFilters) => ['instancias', filters] as const,
}

export function useEncuentros(filters: EncuentrosFilters = {}) {
  return useQuery<SlotEncuentro[]>({
    queryKey: encuentroQueryKeys.encuentros(filters),
    queryFn: () => encuentrosService.getEncuentros(filters),
  })
}

export function useInstancias(filters: EncuentrosFilters = {}) {
  return useQuery<InstanciaEncuentro[]>({
    queryKey: encuentroQueryKeys.instancias(filters),
    queryFn: () => encuentrosService.getInstancias(filters),
  })
}

export function useCreateEncuentro() {
  const queryClient = useQueryClient()
  return useMutation<SlotEncuentro, Error, SlotEncuentroCreate>({
    mutationFn: (payload) => encuentrosService.createEncuentro(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] })
    },
  })
}

export function useUpdateInstancia() {
  const queryClient = useQueryClient()
  return useMutation<InstanciaEncuentro, Error, { id: string; payload: InstanciaEncuentroUpdate }>({
    mutationFn: ({ id, payload }) => encuentrosService.updateInstancia(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instancias'] })
    },
  })
}
