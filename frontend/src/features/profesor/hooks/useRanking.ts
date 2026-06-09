import { useQuery } from '@tanstack/react-query'
import { comisionesService } from '../services/comisionesService'

export function useRanking(materiaId: string) {
  return useQuery({
    queryKey: ['ranking', materiaId] as const,
    queryFn: () => comisionesService.getRanking(materiaId),
    enabled: Boolean(materiaId),
  })
}
