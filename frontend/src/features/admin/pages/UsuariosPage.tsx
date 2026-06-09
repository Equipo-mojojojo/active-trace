/**
 * UsuariosPage — Gestión de usuarios del tenant.
 *
 * Layout (Stitch: Gestión de Usuarios - Admin Portal):
 *  - Header + botón "Nuevo usuario"
 *  - Filtros: búsqueda + filtro por rol
 *  - Tabla: nombre, email, rol badges, estado, acciones
 *  - Drawer lateral: crear/editar usuario con multi-select de roles
 *
 * Spec: frontend-usuarios-admin
 * NOTE: Identity and tenant ALWAYS from JWT session. Never sent as UI params.
 */
import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useUsuarios, useCreateUsuario, useUpdateUsuario } from '../hooks/useUsuarios'
import { EstadoBadge } from '../components/EstadoBadge'
import { RolBadgeAdmin } from '../components/RolBadgeAdmin'
import type { UsuarioTenant, RolUsuario, UsuariosFilters } from '../types/admin.types'

const ALL_ROLES: RolUsuario[] = ['ALUMNO', 'TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS']

const usuarioSchema = z.object({
  nombre: z.string().min(1, 'Requerido'),
  email: z.string().email('Email inválido'),
  roles: z.array(z.enum(['ALUMNO', 'TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS'])).min(1, 'Al menos un rol'),
  activo: z.boolean(),
})
type UsuarioForm = z.infer<typeof usuarioSchema>

export function UsuariosPage() {
  const [filters, setFilters] = useState<UsuariosFilters>({})
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<UsuarioTenant | null>(null)
  const [drawerError, setDrawerError] = useState<string | null>(null)

  const usuariosQuery = useUsuarios(filters)
  const createMut = useCreateUsuario()
  const updateMut = useUpdateUsuario()

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<UsuarioForm>({
    resolver: zodResolver(usuarioSchema),
    defaultValues: { nombre: '', email: '', roles: [], activo: true },
  })

  const openNew = () => {
    setEditingUser(null)
    reset({ nombre: '', email: '', roles: [], activo: true })
    setDrawerError(null)
    setDrawerOpen(true)
  }

  const openEdit = (u: UsuarioTenant) => {
    setEditingUser(u)
    reset({
      nombre: u.nombre,
      email: u.email,
      roles: u.roles,
      activo: u.estado === 'Activo',
    })
    setDrawerError(null)
    setDrawerOpen(true)
  }

  const closeDrawer = () => {
    setDrawerOpen(false)
    setEditingUser(null)
  }

  const onSubmit = async (values: UsuarioForm) => {
    setDrawerError(null)
    try {
      if (editingUser) {
        await updateMut.mutateAsync({
          id: editingUser.id,
          payload: { nombre: values.nombre, roles: values.roles, activo: values.activo },
        })
      } else {
        await createMut.mutateAsync({
          nombre: values.nombre,
          email: values.email,
          roles: values.roles,
          activo: values.activo,
        })
      }
      closeDrawer()
    } catch {
      setDrawerError('Error al guardar el usuario.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Usuarios del Tenant</h1>
          <p className="mt-1 text-sm text-slate-500">Gestión de usuarios y roles</p>
        </div>
        <button
          type="button"
          onClick={openNew}
          aria-label="Nuevo usuario"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nuevo usuario
        </button>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <input
          type="text"
          placeholder="Buscar por nombre o email..."
          value={filters.q ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value || undefined }))}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select
          value={filters.rol ?? ''}
          onChange={(e) =>
            setFilters((f) => ({ ...f, rol: (e.target.value as RolUsuario) || undefined }))
          }
          aria-label="Filtrar por rol"
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Todos los roles</option>
          {ALL_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {/* Tabla */}
      {usuariosQuery.isLoading && <p className="text-sm text-slate-500">Cargando usuarios...</p>}
      {usuariosQuery.isError && <p className="text-sm text-red-600">Error al cargar los usuarios.</p>}

      {usuariosQuery.data && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Roles</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Estado</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {usuariosQuery.data.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">{u.nombre}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {u.roles.map((r) => <RolBadgeAdmin key={r} rol={r} />)}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <EstadoBadge estado={u.estado === 'Activo' ? 'Activa' : 'Inactiva'} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => openEdit(u)}
                      className="text-indigo-600 hover:underline text-sm"
                      aria-label={`Editar usuario ${u.nombre}`}
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
              {usuariosQuery.data.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-slate-500">
                    Sin usuarios para los filtros seleccionados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label="Drawer usuario">
          {/* Backdrop */}
          <div className="flex-1 bg-black/30" onClick={closeDrawer} />
          {/* Panel */}
          <div className="flex h-full w-full max-w-md flex-col bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h2 className="text-base font-semibold text-slate-900">
                {editingUser ? `Editar usuario` : 'Nuevo usuario'}
              </h2>
              <button type="button" onClick={closeDrawer} className="text-slate-400 hover:text-slate-600" aria-label="Cerrar drawer">
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-6">
              {drawerError && (
                <p className="mb-4 text-sm text-red-600" role="alert">{drawerError}</p>
              )}
              <form id="usuario-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Nombre *</label>
                  <input {...register('nombre')} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  {errors.nombre && <p className="mt-0.5 text-xs text-red-600">{errors.nombre.message}</p>}
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Email *</label>
                  <input type="email" {...register('email')} disabled={Boolean(editingUser)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50" />
                  {errors.email && <p className="mt-0.5 text-xs text-red-600">{errors.email.message}</p>}
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Roles * (seleccioná uno o más)</label>
                  <Controller
                    name="roles"
                    control={control}
                    render={({ field }) => (
                      <div className="flex flex-wrap gap-2 rounded-md border border-slate-300 p-3">
                        {ALL_ROLES.map((rol) => {
                          const selected = field.value.includes(rol)
                          return (
                            <button
                              key={rol}
                              type="button"
                              onClick={() => {
                                field.onChange(
                                  selected
                                    ? field.value.filter((r) => r !== rol)
                                    : [...field.value, rol],
                                )
                              }}
                              aria-pressed={selected}
                              className={[
                                'rounded-full px-3 py-1 text-xs font-medium border transition-colors',
                                selected
                                  ? 'border-indigo-600 bg-indigo-600 text-white'
                                  : 'border-slate-300 bg-white text-slate-700 hover:border-indigo-400',
                              ].join(' ')}
                            >
                              {rol}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  />
                  {errors.roles && <p className="mt-0.5 text-xs text-red-600">{errors.roles.message}</p>}
                </div>
                <div className="flex items-center gap-3">
                  <label className="text-xs font-medium text-slate-600">Estado activo</label>
                  <Controller
                    name="activo"
                    control={control}
                    render={({ field }) => (
                      <button
                        type="button"
                        role="switch"
                        aria-checked={field.value}
                        onClick={() => field.onChange(!field.value)}
                        className={[
                          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                          field.value ? 'bg-indigo-600' : 'bg-slate-300',
                        ].join(' ')}
                      >
                        <span className={[
                          'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                          field.value ? 'translate-x-6' : 'translate-x-1',
                        ].join(' ')} />
                      </button>
                    )}
                  />
                </div>
              </form>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button type="button" onClick={closeDrawer} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                Cancelar
              </button>
              <button
                type="submit"
                form="usuario-form"
                disabled={createMut.isPending || updateMut.isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {createMut.isPending || updateMut.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
