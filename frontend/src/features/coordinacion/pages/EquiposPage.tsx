/**
 * EquiposPage — gestión de equipos docentes.
 *
 * Layout (from Stitch screen 9368f556d4584ff4a0cae673ca93eb4e):
 *  - Header con título + botones "Asignación masiva" y "Exportar"
 *  - Filtros por estado y comisiones
 *  - TablaEquipos
 *  - DrawerAsignacion (crear/editar)
 *  - ModalAsignacionMasiva
 *  - Botón "Clonar equipo desde período anterior"
 */
import { useState } from 'react'
import { useEquipos, useDeleteAsignacion, useClonarEquipo } from '../hooks/useEquipos'
import { equiposService } from '../services/equiposService'
import { TablaEquipos } from '../components/TablaEquipos'
import { DrawerAsignacion } from '../components/DrawerAsignacion'
import { ModalAsignacionMasiva } from '../components/ModalAsignacionMasiva'
import type { Asignacion, EquiposFilters } from '../types/coordinacion.types'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function EquiposPage() {
  const [filters, setFilters] = useState<EquiposFilters>({})
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedAsignacion, setSelectedAsignacion] = useState<Asignacion | null>(null)
  const [masivOpen, setMasivOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const equiposQuery = useEquipos(filters)
  const deleteMutation = useDeleteAsignacion()
  const clonarMutation = useClonarEquipo()

  const handleEdit = (asig: Asignacion) => {
    setSelectedAsignacion(asig)
    setDrawerOpen(true)
  }

  const handleNewAsignacion = () => {
    setSelectedAsignacion(null)
    setDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setDrawerOpen(false)
    setSelectedAsignacion(null)
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Seguro que querés eliminar esta asignación?')) return
    setDeletingId(id)
    try {
      await deleteMutation.mutateAsync(id)
    } finally {
      setDeletingId(null)
    }
  }

  const handleExport = async () => {
    const blob = await equiposService.exportEquipos(filters)
    downloadBlob(blob, 'equipos-docentes.csv')
  }

  const handleClonar = async () => {
    const confirmed = window.confirm(
      'Esta acción clonará el equipo docente del período anterior al período actual. ¿Continuás?',
    )
    if (!confirmed) return
    // TODO: in a full implementation, open a dialog to select source/target cohorte
    alert('Funcionalidad de clonar: requiere seleccionar cohorte de origen y destino.')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Equipos Docentes</h1>
          <p className="mt-1 text-sm text-slate-500">
            Asignaciones de docentes por materia y comisión
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleClonar}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Clonar equipo
          </button>
          <button
            type="button"
            onClick={() => setMasivOpen(true)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Asignación masiva
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Exportar
          </button>
          <button
            type="button"
            onClick={handleNewAsignacion}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Asignar docente
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Estado</label>
          <select
            value={filters.estado ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, estado: e.target.value || undefined }))}
            className="w-36 rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Todos</option>
            <option value="Vigente">Vigente</option>
            <option value="Vencida">Vencida</option>
            <option value="Futura">Futura</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Rol</label>
          <select
            value={filters.rol ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, rol: e.target.value || undefined }))}
            className="w-36 rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Todos</option>
            <option value="TUTOR">Tutor</option>
            <option value="PROFESOR">Profesor</option>
            <option value="COORDINADOR">Coordinador</option>
            <option value="NEXO">Nexo</option>
          </select>
        </div>
      </div>

      {/* Tabla */}
      {equiposQuery.isLoading && (
        <p className="text-sm text-slate-500">Cargando asignaciones...</p>
      )}
      {equiposQuery.isError && (
        <p className="text-sm text-red-600">Error al cargar las asignaciones.</p>
      )}
      {!equiposQuery.isLoading && (
        <TablaEquipos
          asignaciones={equiposQuery.data ?? []}
          onEdit={handleEdit}
          onDelete={handleDelete}
          isDeleting={deletingId}
        />
      )}

      {/* Drawer */}
      <DrawerAsignacion
        asignacion={selectedAsignacion}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />

      {/* Modal masiva */}
      <ModalAsignacionMasiva open={masivOpen} onClose={() => setMasivOpen(false)} />
    </div>
  )
}
