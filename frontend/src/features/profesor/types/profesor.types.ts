/**
 * TypeScript types derived from backend Pydantic schemas for the profesor feature.
 *
 * Sources:
 *  - backend/app/schemas/analisis.py
 *  - backend/app/schemas/calificaciones.py
 *  - backend/app/schemas/comunicacion.py
 */

// ─── Calificaciones ───────────────────────────────────────────────────────────

export interface ActividadDetectada {
  nombre: string
  tipo: 'numerica' | 'textual'
  muestra_valores: string[]
}

export interface PreviewCalificacionesResponse {
  actividades: ActividadDetectada[]
}

export interface ImportCalificacionesResponse {
  importadas: number
}

export interface UmbralMateriaRequest {
  asignacion_id: string
  materia_id: string
  umbral_pct: number
  valores_aprobatorios: string[]
}

export interface UmbralMateriaResponse {
  id: string
  asignacion_id: string
  umbral_pct: number
  valores_aprobatorios: string[]
}

// ─── Comision (derived from asignaciones / domain model) ─────────────────────

export interface Comision {
  id: string
  materia_id: string
  materia_nombre: string
  cohorte: string
  comision: string
  total_alumnos: number
  tiene_calificaciones: boolean
}

// ─── Análisis — Atrasados ─────────────────────────────────────────────────────

export interface AlumnoAtrasado {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  materia_id: string
  actividades_faltantes: string[]
  actividades_reprobadas: string[]
}

export interface AtrasadosResponse {
  total: number
  atrasados: AlumnoAtrasado[]
}

// ─── Análisis — Ranking ───────────────────────────────────────────────────────

export interface RankingEntry {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  comision: string | null
  aprobadas: number
}

export interface RankingResponse {
  total: number
  ranking: RankingEntry[]
}

// ─── Análisis — Notas Finales ─────────────────────────────────────────────────

export interface NotaFinalEntry {
  entrada_padron_id: string
  nombre: string
  apellidos: string
  nota_final: number
}

export interface NotasFinalResponse {
  actividades_seleccionadas: string[]
  notas: NotaFinalEntry[]
}

// ─── Análisis — Monitor ───────────────────────────────────────────────────────

export interface MonitorEntry {
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

export interface MonitorResponse {
  total: number
  limit: number
  offset: number
  entries: MonitorEntry[]
}

export interface MonitorFiltros {
  materia_id?: string
  comision?: string
  regional?: string
  q?: string
  min_aprobadas?: number
  limit?: number
  offset?: number
}

// ─── Comunicaciones ───────────────────────────────────────────────────────────

export interface ComunicacionPreviewRequest {
  materia_id: string
  entrada_padron_ids: string[]
  asunto_template: string
  cuerpo_template: string
}

export interface ComunicacionPreviewItem {
  entrada_padron_id: string
  destinatario_nombre: string
  destinatario_email: string
  asunto: string
  cuerpo: string
}

export interface ComunicacionPreviewResponse {
  requiere_aprobacion: boolean
  preview: ComunicacionPreviewItem[]
}

export interface ComunicacionEstado {
  id: string
  lote_id: string
  entrada_padron_id: string
  destinatario_nombre: string
  estado: EstadoComunicacion
  requiere_aprobacion: boolean
  aprobada: boolean
  error_detalle: string | null
}

export interface ComunicacionLoteResponse {
  lote_id: string
  total: number
  requiere_aprobacion: boolean
  comunicaciones: ComunicacionEstado[]
}

export type EstadoComunicacion =
  | 'PENDIENTE'
  | 'ENVIANDO'
  | 'OK'
  | 'FALLIDO'
  | 'CANCELADO'

export const ESTADOS_TERMINALES: EstadoComunicacion[] = ['OK', 'FALLIDO', 'CANCELADO']
