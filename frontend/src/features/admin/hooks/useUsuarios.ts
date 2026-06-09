import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usuariosService } from '../services/usuariosService'
import type { UsuarioTenantCreate, UsuarioTenantUpdate, UsuariosFilters } from '../types/admin.types'

export const usuariosQueryKeys = {
  usuarios: (filters: UsuariosFilters) => ['admin', 'usuarios', filters] as const,
}

export function useUsuarios(filters: UsuariosFilters = {}) {
  return useQuery({
    queryKey: usuariosQueryKeys.usuarios(filters),
    queryFn: () => usuariosService.getUsuarios(filters),
  })
}

export function useCreateUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UsuarioTenantCreate) => usuariosService.createUsuario(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'usuarios'] })
    },
  })
}

export function useUpdateUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UsuarioTenantUpdate }) =>
      usuariosService.updateUsuario(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'usuarios'] })
    },
  })
}
