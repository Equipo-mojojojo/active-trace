import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { avisosService } from '../services/avisosService'
import type { Aviso, AvisoCreate } from '../types/coordinacion.types'

export const avisoQueryKeys = {
  avisos: () => ['avisos'] as const,
  aviso: (id: string) => ['avisos', id] as const,
}

export function useAvisos() {
  return useQuery<Aviso[]>({
    queryKey: avisoQueryKeys.avisos(),
    queryFn: () => avisosService.getAvisos(),
  })
}

export function useCreateAviso() {
  const queryClient = useQueryClient()
  return useMutation<Aviso, Error, AvisoCreate>({
    mutationFn: (payload) => avisosService.createAviso(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}

export function useArchivarAviso() {
  const queryClient = useQueryClient()
  return useMutation<Aviso, Error, string>({
    mutationFn: (id) => avisosService.archivarAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}

export function useAckAviso() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => avisosService.ackAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}
