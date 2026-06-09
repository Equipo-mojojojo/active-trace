import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { coloquiosService } from '../services/coloquiosService'
import type {
  Convocatoria,
  ConvocatoriaCreate,
  ConvocatoriaMetrics,
  Reserva,
  Resultado,
  ResultadoCreate,
} from '../types/coloquios.types'

export const coloquioQueryKeys = {
  coloquios: () => ['coloquios'] as const,
  coloquio: (id: string) => ['coloquios', id] as const,
  metricas: (id: string) => ['coloquios', id, 'metricas'] as const,
  reservas: (id: string) => ['coloquios', id, 'reservas'] as const,
  resultados: (id: string) => ['coloquios', id, 'resultados'] as const,
}

export function useColoquios() {
  return useQuery<Convocatoria[]>({
    queryKey: coloquioQueryKeys.coloquios(),
    queryFn: () => coloquiosService.getColoquios(),
  })
}

export function useConvocatoria(id: string) {
  return useQuery<Convocatoria>({
    queryKey: coloquioQueryKeys.coloquio(id),
    queryFn: () => coloquiosService.getConvocatoriaDetail(id),
    enabled: Boolean(id),
  })
}

export function useConvocatoriaMetricas(id: string) {
  return useQuery<ConvocatoriaMetrics>({
    queryKey: coloquioQueryKeys.metricas(id),
    queryFn: () => coloquiosService.getMetricas(id),
    enabled: Boolean(id),
  })
}

export function useReservas(id: string) {
  return useQuery<Reserva[]>({
    queryKey: coloquioQueryKeys.reservas(id),
    queryFn: () => coloquiosService.getReservas(id),
    enabled: Boolean(id),
  })
}

export function useResultados(id: string) {
  return useQuery<Resultado[]>({
    queryKey: coloquioQueryKeys.resultados(id),
    queryFn: () => coloquiosService.getResultados(id),
    enabled: Boolean(id),
  })
}

export function useCreateConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation<Convocatoria, Error, ConvocatoriaCreate>({
    mutationFn: (payload) => coloquiosService.createConvocatoria(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios'] })
    },
  })
}

export function useSaveResultado() {
  const queryClient = useQueryClient()
  return useMutation<Resultado, Error, { convId: string; payload: ResultadoCreate }>({
    mutationFn: ({ convId, payload }) => coloquiosService.saveResultado(convId, payload),
    onSuccess: (_data, { convId }) => {
      queryClient.invalidateQueries({ queryKey: coloquioQueryKeys.resultados(convId) })
    },
  })
}

export function useCerrarConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation<Convocatoria, Error, string>({
    mutationFn: (id) => coloquiosService.cerrarConvocatoria(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios'] })
    },
  })
}
