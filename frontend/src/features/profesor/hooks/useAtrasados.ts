import { useQuery } from '@tanstack/react-query'
import { comisionesService } from '../services/comisionesService'

export const queryKeys = {
  atrasados: (materiaId: string) => ['atrasados', materiaId] as const,
  ranking: (materiaId: string) => ['ranking', materiaId] as const,
  notasFinales: (materiaId: string) => ['notas-finales', materiaId] as const,
}

export function useAtrasados(materiaId: string) {
  return useQuery({
    queryKey: queryKeys.atrasados(materiaId),
    queryFn: () => comisionesService.getAtrasados(materiaId),
    enabled: Boolean(materiaId),
  })
}
