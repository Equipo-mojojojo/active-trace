import { useQuery } from '@tanstack/react-query'
import { comisionesService } from '../services/comisionesService'

export function useNotasFinales(materiaId: string) {
  return useQuery({
    queryKey: ['notas-finales', materiaId] as const,
    queryFn: () => comisionesService.getNotasFinales(materiaId),
    enabled: Boolean(materiaId),
  })
}
