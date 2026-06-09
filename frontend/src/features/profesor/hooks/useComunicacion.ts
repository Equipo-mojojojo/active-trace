import { useMutation, useQueryClient } from '@tanstack/react-query'
import { comunicacionesService } from '../services/comunicacionesService'
import type { ComunicacionPreviewRequest, ComunicacionLoteResponse } from '../types/profesor.types'

export function useComunicacion(materiaId: string) {
  const queryClient = useQueryClient()

  return useMutation<ComunicacionLoteResponse, Error, ComunicacionPreviewRequest>({
    mutationFn: (payload) => comunicacionesService.enviarComunicacion(payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({
        queryKey: ['comunicaciones', data.lote_id],
      })
    },
  })
}
