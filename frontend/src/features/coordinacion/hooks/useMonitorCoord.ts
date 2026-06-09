import { useQuery } from '@tanstack/react-query'
import { monitorService } from '../services/monitorService'
import type { MonitorCoordResponse, MonitorFilters } from '../types/coordinacion.types'

export const monitorQueryKeys = {
  monitorCoord: (filters: MonitorFilters) => ['monitor-coord', filters] as const,
}

export function useMonitorCoord(filters: MonitorFilters = {}) {
  return useQuery<MonitorCoordResponse>({
    queryKey: monitorQueryKeys.monitorCoord(filters),
    queryFn: () => monitorService.getMonitorCoord(filters),
  })
}
