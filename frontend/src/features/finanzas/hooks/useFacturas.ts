import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { facturasService } from '../services/facturasService'
import type { FacturaCreate, FacturaFilters, EstadoFactura } from '../types/finanzas.types'

export const facturaQueryKeys = {
  facturas: (filters: FacturaFilters) => ['facturas', filters] as const,
}

export function useFacturas(filters: FacturaFilters = {}) {
  return useQuery({
    queryKey: facturaQueryKeys.facturas(filters),
    queryFn: () => facturasService.getFacturas(filters),
  })
}

export function useCrearFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FacturaCreate) => facturasService.crearFactura(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
    },
  })
}

export function useCambiarEstadoFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: EstadoFactura }) =>
      facturasService.cambiarEstado(id, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
    },
  })
}

export function useAdjuntarArchivo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) =>
      facturasService.adjuntarArchivo(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] })
    },
  })
}
