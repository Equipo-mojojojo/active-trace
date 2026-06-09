/**
 * EncuentrosPage — lista global de encuentros + crear nuevo.
 */
import { useState } from 'react'
import { useEncuentros, useInstancias } from '../hooks/useEncuentros'
import { TablaEncuentros } from '../components/TablaEncuentros'
import { ModalNuevoEncuentro } from '../components/ModalNuevoEncuentro'
import { DrawerEditarInstancia } from '../components/DrawerEditarInstancia'
import type { SlotEncuentro, InstanciaEncuentro } from '../types/encuentros.types'

export function EncuentrosPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<SlotEncuentro | null>(null)
  const [selectedInstancia, setSelectedInstancia] = useState<InstanciaEncuentro | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const slotsQuery = useEncuentros()
  const instanciasQuery = useInstancias(
    selectedSlot ? { asignacion_id: selectedSlot.asignacion_id } : {},
  )

  const handleVerInstancias = (slot: SlotEncuentro) => {
    setSelectedSlot(slot)
  }

  const handleEditInstancia = (instancia: InstanciaEncuentro) => {
    setSelectedInstancia(instancia)
    setDrawerOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Encuentros</h1>
          <p className="mt-1 text-sm text-slate-500">Gestión global de encuentros académicos</p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nuevo encuentro
        </button>
      </div>

      {/* Tabla slots */}
      {slotsQuery.isLoading && <p className="text-sm text-slate-500">Cargando encuentros...</p>}
      {slotsQuery.isError && <p className="text-sm text-red-600">Error al cargar los encuentros.</p>}
      {!slotsQuery.isLoading && (
        <TablaEncuentros
          slots={slotsQuery.data ?? []}
          onVerInstancias={handleVerInstancias}
        />
      )}

      {/* Instancias del slot seleccionado */}
      {selectedSlot && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">
              Instancias: {selectedSlot.titulo}
            </h2>
            <button
              type="button"
              onClick={() => setSelectedSlot(null)}
              className="text-sm text-slate-400 hover:text-slate-600"
            >
              Cerrar
            </button>
          </div>

          {instanciasQuery.isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
          {(instanciasQuery.data ?? []).length === 0 && !instanciasQuery.isLoading && (
            <p className="text-sm text-slate-500">Sin instancias para este encuentro.</p>
          )}
          <div className="space-y-2">
            {(instanciasQuery.data ?? []).map((inst) => (
              <div
                key={inst.id}
                className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-medium text-slate-700">{inst.titulo}</p>
                  <p className="text-xs text-slate-400">
                    {inst.fecha} {inst.hora} — {inst.estado}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleEditInstancia(inst)}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
                >
                  Editar
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal nuevo */}
      <ModalNuevoEncuentro open={modalOpen} onClose={() => setModalOpen(false)} />

      {/* Drawer editar instancia */}
      <DrawerEditarInstancia
        instancia={selectedInstancia}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false)
          setSelectedInstancia(null)
        }}
      />
    </div>
  )
}
