import { useQuery } from '@tanstack/react-query'
import { comunicacionesService } from '../services/comunicacionesService'
import { ESTADOS_TERMINALES } from '../types/profesor.types'
import type { EstadoComunicacion } from '../types/profesor.types'

/**
 * Hook for tracking comunicaciones with conditional polling.
 * Polls every 5s while there are non-terminal states (PENDIENTE or ENVIANDO).
 * Stops polling when all are terminal (OK, FALLIDO, CANCELADO).
 */
export function useTrackingComunicaciones(loteId: string | null) {
  return useQuery({
    queryKey: ['comunicaciones', loteId] as const,
    queryFn: () => {
      if (!loteId) return null
      return comunicacionesService.getLote(loteId)
    },
    enabled: Boolean(loteId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 5000

      const hasNonTerminal = data.comunicaciones.some(
        (c) => !ESTADOS_TERMINALES.includes(c.estado as EstadoComunicacion),
      )
      return hasNonTerminal ? 5000 : false
    },
  })
}
