/**
 * AvisosPage — gestión de avisos institucionales.
 *
 * Layout (from Stitch screen 555dba071889406ca47524eed207a5df):
 *  - Header con botón "Publicar aviso"
 *  - Lista de AvisoCard
 *  - DrawerPublicarAviso
 */
import { useState } from 'react'
import { useAvisos, useArchivarAviso, useAckAviso } from '../hooks/useAvisos'
import { AvisoCard } from '../components/AvisoCard'
import { DrawerPublicarAviso } from '../components/DrawerPublicarAviso'
import type { AvisoDetalle } from '../types/coordinacion.types'

export function AvisosPage() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [archivingId, setArchivingId] = useState<string | null>(null)

  const avisosQuery = useAvisos()
  const archivarMutation = useArchivarAviso()
  const ackMutation = useAckAviso()

  const avisos = (avisosQuery.data ?? []).filter((a) => a.activo)

  const handleArchivar = async (id: string) => {
    if (!window.confirm('¿Archivar este aviso? No se mostrará más en la lista activa.')) return
    setArchivingId(id)
    try {
      await archivarMutation.mutateAsync(id)
    } finally {
      setArchivingId(null)
    }
  }

  const handleAck = async (id: string) => {
    await ackMutation.mutateAsync(id)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Avisos institucionales</h1>
          <p className="mt-1 text-sm text-slate-500">
            Publicar y gestionar avisos para docentes, alumnos y coordinadores
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Publicar aviso
        </button>
      </div>

      {/* Content */}
      {avisosQuery.isLoading && (
        <p className="text-sm text-slate-500">Cargando avisos...</p>
      )}
      {avisosQuery.isError && (
        <p className="text-sm text-red-600">Error al cargar los avisos.</p>
      )}
      {!avisosQuery.isLoading && avisos.length === 0 && (
        <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm text-slate-500">No hay avisos activos. Publicá uno nuevo.</p>
        </div>
      )}
      <div className="space-y-4">
        {avisos.map((aviso) => (
          <AvisoCard
            key={aviso.id}
            aviso={aviso as AvisoDetalle}
            onArchivar={handleArchivar}
            onAck={handleAck}
            isArchiving={archivingId === aviso.id}
          />
        ))}
      </div>

      {/* Drawer */}
      <DrawerPublicarAviso open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  )
}
