import { useQuery } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import { monitorService } from '../services/monitorService'
import type { MonitorFiltros } from '@/features/profesor/types/profesor.types'

/**
 * Hook for monitor de seguimiento with debounced search query.
 * Debounce 300ms on the `q` (search by alumno) filter.
 */
export function useMonitor(filtros: MonitorFiltros = {}) {
  const [debouncedQ, setDebouncedQ] = useState(filtros.q ?? '')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setDebouncedQ(filtros.q ?? '')
    }, 300)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [filtros.q])

  const resolvedFiltros: MonitorFiltros = { ...filtros, q: debouncedQ }

  return useQuery({
    queryKey: ['monitor', resolvedFiltros] as const,
    queryFn: () => monitorService.getMonitor(resolvedFiltros),
  })
}
