import { useQuery } from '@tanstack/react-query'
import { encuentrosService } from '../services/encuentrosService'
import type { Guardia, GuardiasFilters } from '../types/encuentros.types'

export const guardiaQueryKeys = {
  guardias: (filters: GuardiasFilters) => ['guardias', filters] as const,
}

export function useGuardias(filters: GuardiasFilters = {}) {
  return useQuery<Guardia[]>({
    queryKey: guardiaQueryKeys.guardias(filters),
    queryFn: () => encuentrosService.getGuardias(filters),
  })
}
