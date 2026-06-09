/**
 * TypeScript types derived from backend Pydantic schemas for the encuentros feature.
 *
 * Sources:
 *  - backend/app/schemas/encuentros.py
 *  - backend/app/schemas/guardias.py
 *  - backend/app/models/enums.py
 */

// ─── Slot de Encuentro ────────────────────────────────────────────────────────

export type EstadoEncuentro = 'Programado' | 'Realizado' | 'Cancelado'
export type DiaSemana = 'Lunes' | 'Martes' | 'Miércoles' | 'Jueves' | 'Viernes' | 'Sábado' | 'Domingo'

export interface SlotEncuentro {
  id: string
  asignacion_id: string
  materia_id: string
  titulo: string
  hora: string // time HH:MM
  dia_semana: DiaSemana
  fecha_inicio: string // date ISO
  cant_semanas: number
  fecha_unica: string | null
  meet_url: string | null
  vig_desde: string
  vig_hasta: string | null
  created_at: string
  updated_at: string
}

export interface SlotEncuentroCreate {
  asignacion_id: string
  materia_id: string
  titulo: string
  hora: string
  dia_semana: DiaSemana
  fecha_inicio: string
  cant_semanas?: number
  fecha_unica?: string
  meet_url?: string
  vig_desde: string
  vig_hasta?: string
}

// ─── Instancia de Encuentro ───────────────────────────────────────────────────

export interface InstanciaEncuentro {
  id: string
  slot_id: string | null
  materia_id: string
  fecha: string // date ISO
  hora: string // time HH:MM
  titulo: string
  estado: EstadoEncuentro
  meet_url: string | null
  video_url: string | null
  comentario: string | null
  created_at: string
  updated_at: string
}

export interface InstanciaEncuentroUpdate {
  estado?: EstadoEncuentro
  meet_url?: string
  video_url?: string
  comentario?: string
}

// ─── Guardia ──────────────────────────────────────────────────────────────────

export type EstadoGuardia = 'Pendiente' | 'Realizada' | 'Cancelada'

export interface Guardia {
  id: string
  asignacion_id: string
  materia_id: string
  carrera_id: string
  cohorte_id: string
  dia: string
  horario: string
  estado: EstadoGuardia
  comentarios: string | null
  created_at: string
  updated_at: string
}

// ─── Filters ──────────────────────────────────────────────────────────────────

export interface EncuentrosFilters {
  materia_id?: string
  asignacion_id?: string
}

export interface GuardiasFilters {
  materia_id?: string
  carrera_id?: string
  cohorte_id?: string
  periodo_desde?: string
  periodo_hasta?: string
  docente?: string
}
