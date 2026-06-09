/**
 * EstructuraAcademicaPage — ABM de carreras, cohortes y materias.
 *
 * Layout (Stitch: Estructura Académica - Admin Portal):
 *  - 3 tabs: Carreras / Cohortes / Materias
 *  - Cada tab con tabla + "Nueva" + inline edit/delete
 *
 * Spec: frontend-estructura-academica
 * D3: Tab-per-entidad en una sola página.
 */
import { useState } from 'react'
import {
  useCarreras, useCreateCarrera, useUpdateCarrera, useDeleteCarrera,
  useCohortes, useCreateCohorte, useUpdateCohorte, useDeleteCohorte,
  useMaterias, useCreateMateria, useUpdateMateria, useDeleteMateria,
} from '../hooks/useEstructura'
import { EstadoBadge } from '../components/EstadoBadge'
import type { Carrera, Cohorte, Materia, EstadoEntidad } from '../types/admin.types'

type TabId = 'carreras' | 'cohortes' | 'materias'

const TABS: { id: TabId; label: string }[] = [
  { id: 'carreras', label: 'Carreras' },
  { id: 'cohortes', label: 'Cohortes' },
  { id: 'materias', label: 'Materias' },
]

// ── Inline edit row helpers ───────────────────────────────────────────────────

interface InlineRowState<T> {
  editingId: string | null
  editValues: Partial<T>
  inlineError: string | null
  newRowOpen: boolean
  newValues: Partial<T>
}

function useInlineRow<T>() {
  const [state, setState] = useState<InlineRowState<T>>({
    editingId: null,
    editValues: {},
    inlineError: null,
    newRowOpen: false,
    newValues: {},
  })
  return { state, setState }
}

// ── Carreras tab ──────────────────────────────────────────────────────────────

function CarrerasTab() {
  const query = useCarreras()
  const createMut = useCreateCarrera()
  const updateMut = useUpdateCarrera()
  const deleteMut = useDeleteCarrera()
  const { state, setState } = useInlineRow<Carrera>()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const startEdit = (c: Carrera) =>
    setState((s) => ({ ...s, editingId: c.id, editValues: { ...c }, inlineError: null }))

  const cancelEdit = () => setState((s) => ({ ...s, editingId: null, inlineError: null }))

  const saveEdit = async () => {
    try {
      await updateMut.mutateAsync({
        id: state.editingId!,
        payload: {
          codigo: state.editValues.codigo ?? '',
          nombre: state.editValues.nombre ?? '',
          estado: state.editValues.estado ?? 'Activa',
        },
      })
      setState((s) => ({ ...s, editingId: null, inlineError: null }))
    } catch (err: unknown) {
      const axErr = err as { response?: { status?: number } }
      setState((s) => ({
        ...s,
        inlineError: axErr.response?.status === 409 ? 'Código duplicado para este tenant.' : 'Error al guardar.',
      }))
    }
  }

  const saveNew = async () => {
    try {
      await createMut.mutateAsync({
        codigo: state.newValues.codigo ?? '',
        nombre: state.newValues.nombre ?? '',
      })
      setState((s) => ({ ...s, newRowOpen: false, newValues: {}, inlineError: null }))
    } catch (err: unknown) {
      const axErr = err as { response?: { status?: number } }
      setState((s) => ({
        ...s,
        inlineError: axErr.response?.status === 409 ? 'Código duplicado para este tenant.' : 'Error al crear.',
      }))
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar esta carrera?')) return
    setDeletingId(id)
    try { await deleteMut.mutateAsync(id) } finally { setDeletingId(null) }
  }

  return (
    <div>
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <span className="text-sm font-medium text-slate-700">Carreras</span>
        <button
          type="button"
          onClick={() => setState((s) => ({ ...s, newRowOpen: true, newValues: {}, inlineError: null }))}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          aria-label="Nueva carrera"
        >
          Nueva carrera
        </button>
      </div>
      {state.inlineError && (
        <div className="bg-red-50 px-5 py-2 text-xs text-red-700">{state.inlineError}</div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Código</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Nombre</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Estado</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {state.newRowOpen && (
              <tr className="bg-indigo-50">
                <td className="px-4 py-2">
                  <input
                    value={state.newValues.codigo ?? ''}
                    onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, codigo: e.target.value } }))}
                    placeholder="Código"
                    className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-4 py-2">
                  <input
                    value={state.newValues.nombre ?? ''}
                    onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, nombre: e.target.value } }))}
                    placeholder="Nombre"
                    className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                  />
                </td>
                <td className="px-4 py-2 text-sm text-slate-500">Activa</td>
                <td className="px-4 py-2 text-right">
                  <button type="button" onClick={saveNew} disabled={createMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">
                    {createMut.isPending ? '...' : 'Guardar'}
                  </button>
                  <button type="button" onClick={() => setState((s) => ({ ...s, newRowOpen: false }))} className="text-xs text-slate-500 hover:underline">
                    Cancelar
                  </button>
                </td>
              </tr>
            )}
            {(query.data ?? []).map((c) =>
              state.editingId === c.id ? (
                <tr key={c.id} className="bg-indigo-50">
                  <td className="px-4 py-2">
                    <input
                      value={state.editValues.codigo ?? ''}
                      onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, codigo: e.target.value } }))}
                      className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      value={state.editValues.nombre ?? ''}
                      onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, nombre: e.target.value } }))}
                      className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <select
                      value={state.editValues.estado ?? 'Activa'}
                      onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, estado: e.target.value as EstadoEntidad } }))}
                      className="rounded border border-slate-300 px-2 py-1 text-sm"
                    >
                      <option value="Activa">Activa</option>
                      <option value="Inactiva">Inactiva</option>
                    </select>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button type="button" onClick={saveEdit} disabled={updateMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">
                      {updateMut.isPending ? '...' : 'Guardar'}
                    </button>
                    <button type="button" onClick={cancelEdit} className="text-xs text-slate-500 hover:underline">Cancelar</button>
                  </td>
                </tr>
              ) : (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-slate-700">{c.codigo}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900">{c.nombre}</td>
                  <td className="whitespace-nowrap px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                    <button type="button" onClick={() => startEdit(c)} className="mr-2 text-indigo-600 hover:underline text-xs">Editar</button>
                    <button type="button" onClick={() => handleDelete(c.id)} disabled={deletingId === c.id} className="text-red-600 hover:underline text-xs disabled:opacity-50">
                      {deletingId === c.id ? '...' : 'Eliminar'}
                    </button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Cohortes tab ──────────────────────────────────────────────────────────────

function CohortesTab() {
  const query = useCohortes()
  const carrerasQuery = useCarreras()
  const createMut = useCreateCohorte()
  const updateMut = useUpdateCohorte()
  const deleteMut = useDeleteCohorte()
  const { state, setState } = useInlineRow<Cohorte>()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const startEdit = (c: Cohorte) =>
    setState((s) => ({ ...s, editingId: c.id, editValues: { ...c }, inlineError: null }))

  const cancelEdit = () => setState((s) => ({ ...s, editingId: null, inlineError: null }))

  const handleSave = async (id: string | null) => {
    const payload = {
      carrera_id: (id ? state.editValues.carrera_id : state.newValues.carrera_id) ?? '',
      nombre: (id ? state.editValues.nombre : state.newValues.nombre) ?? '',
      anio: Number((id ? state.editValues.anio : state.newValues.anio) ?? new Date().getFullYear()),
      vigencia_desde: (id ? state.editValues.vigencia_desde : state.newValues.vigencia_desde) ?? '',
      vigencia_hasta: (id ? state.editValues.vigencia_hasta : state.newValues.vigencia_hasta) ?? undefined,
    }
    try {
      if (id) {
        await updateMut.mutateAsync({ id, payload })
        setState((s) => ({ ...s, editingId: null, inlineError: null }))
      } else {
        await createMut.mutateAsync(payload)
        setState((s) => ({ ...s, newRowOpen: false, newValues: {}, inlineError: null }))
      }
    } catch (err: unknown) {
      const axErr = err as { response?: { status?: number } }
      setState((s) => ({
        ...s,
        inlineError: axErr.response?.status === 409 ? 'Nombre duplicado en esta carrera.' : 'Error al guardar.',
      }))
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar esta cohorte?')) return
    setDeletingId(id)
    try { await deleteMut.mutateAsync(id) } finally { setDeletingId(null) }
  }

  const carreras = carrerasQuery.data ?? []

  return (
    <div>
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <span className="text-sm font-medium text-slate-700">Cohortes</span>
        <button
          type="button"
          onClick={() => setState((s) => ({ ...s, newRowOpen: true, newValues: {}, inlineError: null }))}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nueva cohorte
        </button>
      </div>
      {state.inlineError && (
        <div className="bg-red-50 px-5 py-2 text-xs text-red-700">{state.inlineError}</div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Carrera</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Nombre</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Año</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Vigencia desde</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Vigencia hasta</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Estado</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {state.newRowOpen && (
              <tr className="bg-indigo-50">
                <td className="px-4 py-2">
                  <select
                    value={state.newValues.carrera_id ?? ''}
                    onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, carrera_id: e.target.value } }))}
                    className="rounded border border-slate-300 px-2 py-1 text-sm"
                  >
                    <option value="">— Carrera —</option>
                    {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                  </select>
                </td>
                <td className="px-4 py-2"><input value={state.newValues.nombre ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, nombre: e.target.value } }))} placeholder="Nombre" className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2"><input type="number" value={state.newValues.anio ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, anio: Number(e.target.value) } }))} placeholder="Año" className="w-20 rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2"><input type="date" value={state.newValues.vigencia_desde ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, vigencia_desde: e.target.value } }))} className="rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2"><input type="date" value={state.newValues.vigencia_hasta ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, vigencia_hasta: e.target.value } }))} className="rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2 text-sm text-slate-500">Activa</td>
                <td className="px-4 py-2 text-right">
                  <button type="button" onClick={() => handleSave(null)} disabled={createMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">{createMut.isPending ? '...' : 'Guardar'}</button>
                  <button type="button" onClick={() => setState((s) => ({ ...s, newRowOpen: false }))} className="text-xs text-slate-500 hover:underline">Cancelar</button>
                </td>
              </tr>
            )}
            {(query.data ?? []).map((c) =>
              state.editingId === c.id ? (
                <tr key={c.id} className="bg-indigo-50">
                  <td className="px-4 py-2">
                    <select value={state.editValues.carrera_id ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, carrera_id: e.target.value } }))} className="rounded border border-slate-300 px-2 py-1 text-sm">
                      {carreras.map((cr) => <option key={cr.id} value={cr.id}>{cr.nombre}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-2"><input value={state.editValues.nombre ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, nombre: e.target.value } }))} className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><input type="number" value={state.editValues.anio ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, anio: Number(e.target.value) } }))} className="w-20 rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><input type="date" value={state.editValues.vigencia_desde ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, vigencia_desde: e.target.value } }))} className="rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><input type="date" value={state.editValues.vigencia_hasta ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, vigencia_hasta: e.target.value } }))} className="rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><select value={state.editValues.estado ?? 'Activa'} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, estado: e.target.value as EstadoEntidad } }))} className="rounded border border-slate-300 px-2 py-1 text-sm"><option value="Activa">Activa</option><option value="Inactiva">Inactiva</option></select></td>
                  <td className="px-4 py-2 text-right">
                    <button type="button" onClick={() => handleSave(c.id)} disabled={updateMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">{updateMut.isPending ? '...' : 'Guardar'}</button>
                    <button type="button" onClick={cancelEdit} className="text-xs text-slate-500 hover:underline">Cancelar</button>
                  </td>
                </tr>
              ) : (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{c.nombre_carrera ?? c.carrera_id}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900">{c.nombre}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-700">{c.anio}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{c.vigencia_desde}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{c.vigencia_hasta ?? '—'}</td>
                  <td className="whitespace-nowrap px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                    <button type="button" onClick={() => startEdit(c)} className="mr-2 text-indigo-600 hover:underline text-xs">Editar</button>
                    <button type="button" onClick={() => handleDelete(c.id)} disabled={deletingId === c.id} className="text-red-600 hover:underline text-xs disabled:opacity-50">{deletingId === c.id ? '...' : 'Eliminar'}</button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Materias tab ──────────────────────────────────────────────────────────────

function MateriasTab() {
  const query = useMaterias()
  const createMut = useCreateMateria()
  const updateMut = useUpdateMateria()
  const deleteMut = useDeleteMateria()
  const { state, setState } = useInlineRow<Materia>()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const startEdit = (m: Materia) =>
    setState((s) => ({ ...s, editingId: m.id, editValues: { ...m }, inlineError: null }))

  const cancelEdit = () => setState((s) => ({ ...s, editingId: null, inlineError: null }))

  const handleSave = async (id: string | null) => {
    const vals = id ? state.editValues : state.newValues
    try {
      if (id) {
        await updateMut.mutateAsync({
          id,
          payload: {
            codigo: vals.codigo ?? '',
            nombre: vals.nombre ?? '',
            estado: vals.estado ?? 'Activa',
            grupo_plus_clave: vals.grupo_plus_clave ?? undefined,
          },
        })
        setState((s) => ({ ...s, editingId: null, inlineError: null }))
      } else {
        await createMut.mutateAsync({ codigo: vals.codigo ?? '', nombre: vals.nombre ?? '' })
        setState((s) => ({ ...s, newRowOpen: false, newValues: {}, inlineError: null }))
      }
    } catch (err: unknown) {
      const axErr = err as { response?: { status?: number } }
      setState((s) => ({
        ...s,
        inlineError: axErr.response?.status === 409 ? 'Código duplicado.' : 'Error al guardar.',
      }))
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar esta materia?')) return
    setDeletingId(id)
    try { await deleteMut.mutateAsync(id) } finally { setDeletingId(null) }
  }

  return (
    <div>
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <span className="text-sm font-medium text-slate-700">Materias</span>
        <button
          type="button"
          onClick={() => setState((s) => ({ ...s, newRowOpen: true, newValues: {}, inlineError: null }))}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nueva materia
        </button>
      </div>
      {state.inlineError && (
        <div className="bg-red-50 px-5 py-2 text-xs text-red-700">{state.inlineError}</div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Código</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Nombre</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Estado</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Grupo Plus</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {state.newRowOpen && (
              <tr className="bg-indigo-50">
                <td className="px-4 py-2"><input value={state.newValues.codigo ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, codigo: e.target.value } }))} placeholder="Código" className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2"><input value={state.newValues.nombre ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, nombre: e.target.value } }))} placeholder="Nombre" className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2 text-sm text-slate-500">Activa</td>
                <td className="px-4 py-2"><input value={state.newValues.grupo_plus_clave ?? ''} onChange={(e) => setState((s) => ({ ...s, newValues: { ...s.newValues, grupo_plus_clave: e.target.value } }))} placeholder="Clave plus" className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                <td className="px-4 py-2 text-right">
                  <button type="button" onClick={() => handleSave(null)} disabled={createMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">{createMut.isPending ? '...' : 'Guardar'}</button>
                  <button type="button" onClick={() => setState((s) => ({ ...s, newRowOpen: false }))} className="text-xs text-slate-500 hover:underline">Cancelar</button>
                </td>
              </tr>
            )}
            {(query.data ?? []).map((m) =>
              state.editingId === m.id ? (
                <tr key={m.id} className="bg-indigo-50">
                  <td className="px-4 py-2"><input value={state.editValues.codigo ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, codigo: e.target.value } }))} className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><input value={state.editValues.nombre ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, nombre: e.target.value } }))} className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2"><select value={state.editValues.estado ?? 'Activa'} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, estado: e.target.value as EstadoEntidad } }))} className="rounded border border-slate-300 px-2 py-1 text-sm"><option value="Activa">Activa</option><option value="Inactiva">Inactiva</option></select></td>
                  <td className="px-4 py-2"><input value={state.editValues.grupo_plus_clave ?? ''} onChange={(e) => setState((s) => ({ ...s, editValues: { ...s.editValues, grupo_plus_clave: e.target.value } }))} placeholder="Clave plus" className="w-full rounded border border-slate-300 px-2 py-1 text-sm" /></td>
                  <td className="px-4 py-2 text-right">
                    <button type="button" onClick={() => handleSave(m.id)} disabled={updateMut.isPending} className="mr-2 rounded bg-indigo-600 px-2 py-1 text-xs text-white">{updateMut.isPending ? '...' : 'Guardar'}</button>
                    <button type="button" onClick={cancelEdit} className="text-xs text-slate-500 hover:underline">Cancelar</button>
                  </td>
                </tr>
              ) : (
                <tr key={m.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-slate-700">{m.codigo}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900">{m.nombre}</td>
                  <td className="whitespace-nowrap px-4 py-3"><EstadoBadge estado={m.estado} /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{m.grupo_plus_clave ?? '—'}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                    <button type="button" onClick={() => startEdit(m)} className="mr-2 text-indigo-600 hover:underline text-xs">Editar</button>
                    <button type="button" onClick={() => handleDelete(m.id)} disabled={deletingId === m.id} className="text-red-600 hover:underline text-xs disabled:opacity-50">{deletingId === m.id ? '...' : 'Eliminar'}</button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function EstructuraAcademicaPage() {
  const [activeTab, setActiveTab] = useState<TabId>('carreras')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Estructura Académica</h1>
        <p className="mt-1 text-sm text-slate-500">Gestión de carreras, cohortes y materias del tenant</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {/* Tabs */}
        <div className="border-b border-slate-200">
          <nav className="flex" aria-label="Estructura académica">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                aria-selected={activeTab === tab.id}
                role="tab"
                className={[
                  'px-6 py-3 text-sm font-medium transition-colors',
                  activeTab === tab.id
                    ? 'border-b-2 border-indigo-600 text-indigo-600'
                    : 'text-slate-500 hover:text-slate-700',
                ].join(' ')}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div role="tabpanel">
          {activeTab === 'carreras' && <CarrerasTab />}
          {activeTab === 'cohortes' && <CohortesTab />}
          {activeTab === 'materias' && <MateriasTab />}
        </div>
      </div>
    </div>
  )
}
