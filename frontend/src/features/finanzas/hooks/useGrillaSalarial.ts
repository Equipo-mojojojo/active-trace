import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { grillaSalarialService } from '../services/grillaSalarialService'
import type {
  SalarioBaseCreate,
  SalarioPlusCreate,
  SalarioPlusFilters,
} from '../types/finanzas.types'

export const grillaQueryKeys = {
  salarioBase: () => ['grilla-salarial', 'base'] as const,
  salarioPlus: (filters: SalarioPlusFilters) => ['grilla-salarial', 'plus', filters] as const,
}

export function useSalarioBase() {
  return useQuery({
    queryKey: grillaQueryKeys.salarioBase(),
    queryFn: () => grillaSalarialService.getSalariosBase(),
  })
}

export function useCreateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioBaseCreate) => grillaSalarialService.createSalarioBase(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'base'] })
    },
  })
}

export function useUpdateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioBaseCreate }) =>
      grillaSalarialService.updateSalarioBase(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'base'] })
    },
  })
}

export function useDeleteSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => grillaSalarialService.deleteSalarioBase(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'base'] })
    },
  })
}

export function useSalarioPlus(filters: SalarioPlusFilters = {}) {
  return useQuery({
    queryKey: grillaQueryKeys.salarioPlus(filters),
    queryFn: () => grillaSalarialService.getSalariosPlus(filters),
  })
}

export function useCreateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SalarioPlusCreate) => grillaSalarialService.createSalarioPlus(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'plus'] })
    },
  })
}

export function useUpdateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SalarioPlusCreate }) =>
      grillaSalarialService.updateSalarioPlus(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'plus'] })
    },
  })
}

export function useDeleteSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => grillaSalarialService.deleteSalarioPlus(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grilla-salarial', 'plus'] })
    },
  })
}
