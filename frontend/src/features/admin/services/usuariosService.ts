/**
 * Service for gestión de usuarios del tenant.
 *
 * Endpoint path assumed from C-04 conventions: /api/admin/usuarios
 * (confirmed as the standard admin user management path for tenant).
 *
 * Endpoints:
 *  GET   /api/admin/usuarios       — List users of tenant
 *  POST  /api/admin/usuarios       — Create user
 *  PUT   /api/admin/usuarios/{id}  — Update user (roles, estado)
 *
 * Note: Identity and tenant ALWAYS come from JWT session (backend).
 * The UI NEVER sends actor_id or tenant_id as request params.
 */
import { api } from '@/shared/services/api'
import type {
  UsuarioTenant,
  UsuarioTenantCreate,
  UsuarioTenantUpdate,
  UsuariosFilters,
} from '../types/admin.types'

export const usuariosService = {
  async getUsuarios(filters: UsuariosFilters = {}): Promise<UsuarioTenant[]> {
    const { data } = await api.get<UsuarioTenant[]>('/api/admin/usuarios', {
      params: filters,
    })
    return data
  },

  async createUsuario(payload: UsuarioTenantCreate): Promise<UsuarioTenant> {
    const { data } = await api.post<UsuarioTenant>('/api/admin/usuarios', payload)
    return data
  },

  async updateUsuario(id: string, payload: UsuarioTenantUpdate): Promise<UsuarioTenant> {
    const { data } = await api.put<UsuarioTenant>(`/api/admin/usuarios/${id}`, payload)
    return data
  },
}
