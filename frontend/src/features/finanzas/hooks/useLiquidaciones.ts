import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { liquidacionesService } from '../services/liquidacionesService'
import type { LiquidacionFilters } from '../types/finanzas.types'

export const liquidacionQueryKeys = {
  liquidacion: (filters: LiquidacionFilters) => ['liquidaciones', filters] as const,
  historial: () => ['liquidaciones', 'historial'] as const,
}

export function useLiquidaciones(filters: LiquidacionFilters) {
  return useQuery({
    queryKey: liquidacionQueryKeys.liquidacion(filters),
    queryFn: () => liquidacionesService.getLiquidaciones(filters),
    enabled: Boolean(filters.periodo),
  })
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (periodo: string) => liquidacionesService.cerrarLiquidacion(periodo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones'] })
    },
  })
}

export function useHistorialLiquidaciones() {
  return useQuery({
    queryKey: liquidacionQueryKeys.historial(),
    queryFn: () => liquidacionesService.getHistorial(),
  })
}
