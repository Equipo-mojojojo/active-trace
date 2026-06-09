/**
 * TypeScript types derived from backend Pydantic schemas for the coordinacion feature.
 *
 * Sources:
 *  - backend/app/schemas/equipos.py
 *  - backend/app/schemas/avisos.py
 *  - backend/app/schemas/tareas.py
 *  - backend/app/schemas/analisis.py
 *  - backend/app/models/enums.py
 */

// ─── Equipos / Asignaciones ───────────────────────────────────────────────────

export type EstadoVigencia = 'Vigente' | 'Vencida' | 'Futura'

export interface Asignacion {
  id: string
  tenant_id: string
  usuario_id: string
  nombre_usuario: string | null
  rol: string
  materia_id: string | null
  carrera_id: string | null
  cohorte_id: string | null
  comisiones: string | null
  desde: string // date ISO
  hasta: string | null
  responsable_id: string | null
  estado_vigencia: EstadoVigencia
  created_at: string
  updated_at: string
}

export interface AsignacionCreate {
  usuario_id: string
  rol: string
  materia_id?: string
  carrera_id?: string
  cohorte_id?: string
  comisiones?: string
  responsable_id?: string
  desde: string
  hasta?: string
}

export interface AsignacionMasivaRequest {
  usuarios: string[]
  rol: string
  materia_id?: string
  carrera_id?: string
  cohorte_id?: string
  comisiones?: string
  responsable_id?: string
  desde: string
  hasta?: string
}

export interface AsignacionMasivaResponse {
  creadas: number
  asignaciones: Asignacion[]
}

export interface ClonarEquipoRequest {
  materia_id: string
  carrera_id: string
  cohorte_id_origen: string
  cohorte_id_destino: string
  desde: string
  hasta?: string
}

export interface ClonarEquipoResponse {
  clonadas: number
  mensaje: string
  asignaciones: Asignacion[]
}

export interface EquiposFilters {
  estado?: string
  materia_id?: string
  rol?: string
  carrera_id?: string
  cohorte_id?: string
}

// ─── Avisos ───────────────────────────────────────────────────────────────────

export type AlcanceAviso = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol'
export type SeveridadAviso = 'Info' | 'Advertencia' | 'Crítico'

export interface Aviso {
  id: string
  alcance: AlcanceAviso
  materia_id: string | null
  cohorte_id: string | null
  rol_destino: string | null
  severidad: SeveridadAviso
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en: string | null
  orden: number
  activo: boolean
  requiere_ack: boolean
}

export interface AvisoDetalle extends Aviso {
  total_acks: number
  total_visibles: number
}

export interface AvisoCreate {
  alcance: AlcanceAviso
  materia_id?: string
  cohorte_id?: string
  rol_destino?: string
  severidad: SeveridadAviso
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en?: string
  orden?: number
  activo?: boolean
  requiere_ack?: boolean
}

// ─── Tareas ───────────────────────────────────────────────────────────────────

export type EstadoTarea = 'Pendiente' | 'En progreso' | 'Resuelta' | 'Cancelada'

export interface Tarea {
  id: string
  materia_id: string | null
  asignado_a: string
  asignado_por: string
  estado: EstadoTarea
  descripcion: string
  contexto_id: string | null
}

export interface TareaCreate {
  asignado_a: string
  descripcion: string
  materia_id?: string
  contexto_id?: string
}

export interface ComentarioTarea {
  id: string
  tarea_id: string
  autor_id: string
  texto: string
  creado_at: string
}

export interface ComentarioCreate {
  texto: string
}

// ─── Monitor Coordinacion (F2.9) ──────────────────────────────────────────────

export interface MonitorAlumno {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  regional: string | null
  materia_id: string
  aprobadas: number
  reprobadas: number
  faltantes: number
  atrasado: boolean
}

export interface MonitorCoordResponse {
  total: number
  limit: number
  offset: number
  entries: MonitorAlumno[]
}

export interface MonitorFilters {
  materia_id?: string
  comision?: string
  regional?: string
  q?: string
  fecha_desde?: string
  fecha_hasta?: string
  carrera_id?: string
  docente?: string
  estado?: 'todos' | 'atrasados' | 'al_dia'
  limit?: number
  offset?: number
}
