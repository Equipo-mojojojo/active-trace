/**
 * TypeScript types for the admin feature.
 *
 * Sources:
 *  - estructura-carreras, estructura-cohortes, estructura-materias specs (C-06/C-07)
 *  - metricas-panel-auditoria spec (C-19)
 *  - usuarios admin: /api/admin/usuarios (path confirmed with C-04)
 */

// ─── Roles ────────────────────────────────────────────────────────────────────

export type RolUsuario = 'ALUMNO' | 'TUTOR' | 'PROFESOR' | 'COORDINADOR' | 'NEXO' | 'ADMIN' | 'FINANZAS'

// ─── Estructura académica ─────────────────────────────────────────────────────

export type EstadoEntidad = 'Activa' | 'Inactiva'

export interface Carrera {
  id: string
  codigo: string
  nombre: string
  estado: EstadoEntidad
}

export interface CarreraCreate {
  codigo: string
  nombre: string
  estado?: EstadoEntidad
}

export interface Cohorte {
  id: string
  carrera_id: string
  nombre_carrera: string | null
  nombre: string
  anio: number
  vigencia_desde: string
  vigencia_hasta: string | null
  estado: EstadoEntidad
}

export interface CohorteCreate {
  carrera_id: string
  nombre: string
  anio: number
  vigencia_desde: string
  vigencia_hasta?: string
  estado?: EstadoEntidad
}

export interface Materia {
  id: string
  codigo: string
  nombre: string
  estado: EstadoEntidad
  grupo_plus_clave: string | null
}

export interface MateriaCreate {
  codigo: string
  nombre: string
  estado?: EstadoEntidad
  grupo_plus_clave?: string
}

// ─── Usuarios del tenant ──────────────────────────────────────────────────────

export type EstadoUsuario = 'Activo' | 'Inactivo'

export interface UsuarioTenant {
  id: string
  nombre: string
  email: string
  roles: RolUsuario[]
  estado: EstadoUsuario
}

export interface UsuarioTenantCreate {
  nombre: string
  email: string
  roles: RolUsuario[]
  activo?: boolean
}

export interface UsuarioTenantUpdate {
  nombre?: string
  roles?: RolUsuario[]
  activo?: boolean
}

export interface UsuariosFilters {
  rol?: RolUsuario
  q?: string
}

// ─── Auditoría ────────────────────────────────────────────────────────────────

export interface AuditoriaFilters {
  desde?: string
  hasta?: string
  actor_id?: string
  materia_id?: string
  accion?: string
}

export interface AccionPorDia {
  fecha: string
  total: number
}

export interface EstadoComunicacionDocente {
  docente_id: string
  nombre_docente: string
  pendiente: number
  enviando: number
  enviado: number
  error: number
  cancelado: number
}

export interface InteraccionDocente {
  docente_id: string
  nombre_docente: string
  materia_id: string
  nombre_materia: string
  accion: string
  total: number
}

export interface UltimaAccion {
  id: string
  timestamp: string
  actor_id: string
  nombre_actor: string
  materia_id: string | null
  nombre_materia: string | null
  accion: string
  registros_afectados: number
  ip: string | null
  user_agent: string | null
}
