/**
 * TypeScript types derived from backend Pydantic schemas for the coloquios feature.
 *
 * Sources:
 *  - backend/app/schemas/evaluaciones.py
 *  - backend/app/schemas/reservas.py
 *  - backend/app/schemas/resultados.py
 *  - backend/app/models/enums.py
 */

// ─── Turno de Evaluación ──────────────────────────────────────────────────────

export interface TurnoEvaluacion {
  id: string
  evaluacion_id: string
  fecha: string // date ISO
  hora: string // time HH:MM
  max_cupo: number
}

export interface TurnoEvaluacionCreate {
  fecha: string
  hora: string
  max_cupo?: number
}

// ─── Convocatoria (Evaluacion) ────────────────────────────────────────────────

export type EstadoEvaluacion = 'Abierta' | 'Cerrada'
export type TipoEvaluacion = 'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio'

export interface Convocatoria {
  id: string
  materia_id: string
  cohorte_id: string
  tipo: TipoEvaluacion
  instancia: string
  dias_disponibles: number
  estado: EstadoEvaluacion
  turnos: TurnoEvaluacion[]
}

export interface ConvocatoriaCreate {
  materia_id: string
  cohorte_id: string
  tipo: TipoEvaluacion
  instancia: string
  dias_disponibles?: number
  turnos: TurnoEvaluacionCreate[]
}

export interface ConvocatoriaMetrics {
  evaluacion_id: string
  convocados: number
  reservas: number
  libres: number
}

// ─── Convocados ───────────────────────────────────────────────────────────────

export interface Convocado {
  id: string
  evaluacion_id: string
  alumno_id: string
}

export interface ConvocadoImport {
  alumno_ids: string[]
}

// ─── Reservas ─────────────────────────────────────────────────────────────────

export type EstadoReserva = 'Activa' | 'Cancelada'

export interface Reserva {
  id: string
  turno_id: string
  alumno_id: string
  estado: EstadoReserva
  fecha?: string
  hora?: string
}

// ─── Resultados ───────────────────────────────────────────────────────────────

export interface Resultado {
  id: string
  evaluacion_id: string
  alumno_id: string
  nota_final: string | null
}

export interface ResultadoCreate {
  alumno_id: string
  nota_final?: string
}
