/**
 * AvisoCard — card de aviso institucional.
 *
 * Diseño (from Stitch screen 555dba071889406ca47524eed207a5df):
 *  - Título con badge de severidad (Info=azul/Advertencia=naranja/Crítico=rojo)
 *  - Badge de alcance (Global/PorMateria/PorCohorte/PorRol)
 *  - Fechas de vigencia
 *  - Counter de acknowledgment (si requiere_ack)
 *  - Botones Editar / Archivar
 *  - Fondo destacado rojo suave para severidad Crítico
 */
import type { AvisoDetalle, SeveridadAviso, AlcanceAviso } from '../types/coordinacion.types'

interface Props {
  aviso: AvisoDetalle
  onArchivar: (id: string) => void
  onAck?: (id: string) => void
  isArchiving?: boolean
}

function severidadBadge(sev: SeveridadAviso) {
  const map: Record<SeveridadAviso, string> = {
    Info: 'bg-blue-100 text-blue-700',
    Advertencia: 'bg-amber-100 text-amber-700',
    Crítico: 'bg-red-100 text-red-700',
  }
  return map[sev]
}

function alcanceBadge(alcance: AlcanceAviso) {
  const labels: Record<AlcanceAviso, string> = {
    Global: 'Global',
    PorMateria: 'Por materia',
    PorCohorte: 'Por cohorte',
    PorRol: 'Por rol',
  }
  return labels[alcance]
}

function cardBackground(sev: SeveridadAviso) {
  return sev === 'Crítico' ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-white'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function AvisoCard({ aviso, onArchivar, onAck, isArchiving }: Props) {
  return (
    <div
      className={`rounded-lg border p-5 shadow-sm ${cardBackground(aviso.severidad)}`}
    >
      <div className="flex items-start justify-between gap-4">
        {/* Left content */}
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">{aviso.titulo}</h3>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${severidadBadge(aviso.severidad)}`}
            >
              {aviso.severidad}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
              {alcanceBadge(aviso.alcance)}
            </span>
          </div>

          <p className="text-sm text-slate-600">{aviso.cuerpo}</p>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <span>
              Desde: {formatDate(aviso.inicio_en)}
              {aviso.fin_en ? ` — Hasta: ${formatDate(aviso.fin_en)}` : ''}
            </span>
            {aviso.requiere_ack && (
              <span className="font-medium text-slate-500">
                {aviso.total_acks}/{aviso.total_visibles} confirmaron lectura
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex shrink-0 items-center gap-2">
          {aviso.requiere_ack && onAck && (
            <button
              type="button"
              onClick={() => onAck(aviso.id)}
              className="rounded border border-indigo-300 px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
            >
              Confirmar lectura
            </button>
          )}
          <button
            type="button"
            onClick={() => onArchivar(aviso.id)}
            disabled={isArchiving}
            className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-40"
          >
            {isArchiving ? 'Archivando...' : 'Archivar'}
          </button>
        </div>
      </div>
    </div>
  )
}
