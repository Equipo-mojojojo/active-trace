/**
 * GrillaSalarialPage — Gestión de salarios base y plus.
 *
 * Layout (Stitch: Grilla Salarial - Finanzas):
 *  - Card "Salario base por rol" (tabla + Nueva fila + inline edit/delete)
 *  - Card "Plus por grupo" (tabla + filtros + inline edit/delete)
 *
 * Spec: frontend-grilla-salarial
 * D4: Inline edit para filas.
 */
import { useState } from 'react'
import {
  useSalarioBase,
  useCreateSalarioBase,
  useUpdateSalarioBase,
  useDeleteSalarioBase,
  useSalarioPlus,
  useCreateSalarioPlus,
  useUpdateSalarioPlus,
  useDeleteSalarioPlus,
} from '../hooks/useGrillaSalarial'
import { FilaEditable } from '../components/FilaEditable'
import { RolBadge } from '../components/RolBadge'
import type { SalarioBase, SalarioPlus, SalarioPlusFilters, RolDocente } from '../types/finanzas.types'

const ROL_OPTIONS = [
  { value: 'PROFESOR', label: 'Profesor' },
  { value: 'TUTOR', label: 'Tutor' },
  { value: 'COORDINADOR', label: 'Coordinador' },
  { value: 'NEXO', label: 'Nexo' },
]

const SALARIO_BASE_FIELDS = [
  { key: 'rol', label: 'Rol', type: 'select' as const, options: ROL_OPTIONS, required: true },
  { key: 'monto', label: 'Monto', type: 'number' as const, required: true },
  { key: 'vigencia_desde', label: 'Desde', type: 'date' as const, required: true },
  { key: 'vigencia_hasta', label: 'Hasta (vacío = abierta)', type: 'date' as const },
]

const SALARIO_PLUS_FIELDS = [
  { key: 'clave', label: 'Clave/Grupo', type: 'text' as const, required: true },
  { key: 'rol', label: 'Rol', type: 'select' as const, options: ROL_OPTIONS, required: true },
  { key: 'descripcion', label: 'Descripción', type: 'text' as const },
  { key: 'monto', label: 'Monto', type: 'number' as const, required: true },
  { key: 'vigencia_desde', label: 'Desde', type: 'date' as const, required: true },
  { key: 'vigencia_hasta', label: 'Hasta (vacío = abierta)', type: 'date' as const },
]

function toSalarioBaseValues(s: SalarioBase): Record<string, string> {
  return {
    rol: s.rol,
    monto: String(s.monto),
    vigencia_desde: s.vigencia_desde,
    vigencia_hasta: s.vigencia_hasta ?? '',
  }
}

function toSalarioPlusValues(s: SalarioPlus): Record<string, string> {
  return {
    clave: s.clave,
    rol: s.rol,
    descripcion: s.descripcion,
    monto: String(s.monto),
    vigencia_desde: s.vigencia_desde,
    vigencia_hasta: s.vigencia_hasta ?? '',
  }
}

export function GrillaSalarialPage() {
  const [showNewBase, setShowNewBase] = useState(false)
  const [showNewPlus, setShowNewPlus] = useState(false)
  const [plusFilters, setPlusFilters] = useState<SalarioPlusFilters>({})
  const [deletingBaseId, setDeletingBaseId] = useState<string | null>(null)
  const [deletingPlusId, setDeletingPlusId] = useState<string | null>(null)

  const salarioBaseQuery = useSalarioBase()
  const createBase = useCreateSalarioBase()
  const updateBase = useUpdateSalarioBase()
  const deleteBase = useDeleteSalarioBase()

  const salarioPlusQuery = useSalarioPlus(plusFilters)
  const createPlus = useCreateSalarioPlus()
  const updatePlus = useUpdateSalarioPlus()
  const deletePlus = useDeleteSalarioPlus()

  const handleSaveBase = (id: string | null, values: Record<string, string>) => {
    const payload = {
      rol: values['rol'] as RolDocente,
      monto: Number(values['monto']),
      vigencia_desde: values['vigencia_desde'],
      vigencia_hasta: values['vigencia_hasta'] || undefined,
    }
    if (id) return updateBase.mutateAsync({ id, payload })
    return createBase.mutateAsync(payload).then(() => setShowNewBase(false))
  }

  const handleDeleteBase = async (id: string) => {
    if (!window.confirm('¿Eliminar este salario base?')) return
    setDeletingBaseId(id)
    try { await deleteBase.mutateAsync(id) } finally { setDeletingBaseId(null) }
  }

  const handleSavePlus = (id: string | null, values: Record<string, string>) => {
    const payload = {
      clave: values['clave'],
      rol: values['rol'] as RolDocente,
      descripcion: values['descripcion'] ?? '',
      monto: Number(values['monto']),
      vigencia_desde: values['vigencia_desde'],
      vigencia_hasta: values['vigencia_hasta'] || undefined,
    }
    if (id) return updatePlus.mutateAsync({ id, payload })
    return createPlus.mutateAsync(payload).then(() => setShowNewPlus(false))
  }

  const handleDeletePlus = async (id: string) => {
    if (!window.confirm('¿Eliminar este plus?')) return
    setDeletingPlusId(id)
    try { await deletePlus.mutateAsync(id) } finally { setDeletingPlusId(null) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Grilla Salarial</h1>
        <p className="mt-1 text-sm text-slate-500">Configuración de salarios base y plus por rol</p>
      </div>

      {/* Card Salario Base */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-900">Salario base por rol</h2>
          <button
            type="button"
            onClick={() => setShowNewBase(true)}
            aria-label="Nueva fila salario base"
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Nueva fila
          </button>
        </div>
        {salarioBaseQuery.isLoading && <p className="p-4 text-sm text-slate-500">Cargando...</p>}
        {salarioBaseQuery.isError && <p className="p-4 text-sm text-red-600">Error al cargar.</p>}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Rol</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Monto</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Desde</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Hasta</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {showNewBase && (
                <FilaEditable
                  fields={SALARIO_BASE_FIELDS}
                  initialValues={{ rol: '', monto: '', vigencia_desde: '', vigencia_hasta: '' }}
                  displayRow={<></>}
                  startEditing={true}
                  onSave={(v) => handleSaveBase(null, v)}
                />
              )}
              {(salarioBaseQuery.data ?? []).map((s) => (
                <FilaEditable
                  key={s.id}
                  fields={SALARIO_BASE_FIELDS}
                  initialValues={toSalarioBaseValues(s)}
                  displayRow={
                    <>
                      <td className="whitespace-nowrap px-4 py-3"><RolBadge rol={s.rol} /></td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                        {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(s.monto)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{s.vigencia_desde}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{s.vigencia_hasta ?? '—'}</td>
                    </>
                  }
                  onSave={(v) => handleSaveBase(s.id, v)}
                  onDelete={() => handleDeleteBase(s.id)}
                  isDeleting={deletingBaseId === s.id}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card Plus */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-900">Plus por grupo</h2>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={plusFilters.clave ?? ''}
              onChange={(e) => setPlusFilters((f) => ({ ...f, clave: e.target.value || undefined }))}
              className="rounded-md border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="">Todos los grupos</option>
            </select>
            <select
              value={plusFilters.rol ?? ''}
              onChange={(e) => setPlusFilters((f) => ({ ...f, rol: e.target.value || undefined }))}
              className="rounded-md border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="">Todos los roles</option>
              {ROL_OPTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
            <button
              type="button"
              onClick={() => setShowNewPlus(true)}
              aria-label="Nueva fila plus"
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Nueva fila
            </button>
          </div>
        </div>
        {salarioPlusQuery.isLoading && <p className="p-4 text-sm text-slate-500">Cargando...</p>}
        {salarioPlusQuery.isError && <p className="p-4 text-sm text-red-600">Error al cargar.</p>}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Clave</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Rol</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Descripción</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Monto</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Desde</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Hasta</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {showNewPlus && (
                <FilaEditable
                  fields={SALARIO_PLUS_FIELDS}
                  initialValues={{ clave: '', rol: '', descripcion: '', monto: '', vigencia_desde: '', vigencia_hasta: '' }}
                  displayRow={<></>}
                  startEditing={true}
                  onSave={(v) => handleSavePlus(null, v)}
                />
              )}
              {(salarioPlusQuery.data ?? []).map((s) => (
                <FilaEditable
                  key={s.id}
                  fields={SALARIO_PLUS_FIELDS}
                  initialValues={toSalarioPlusValues(s)}
                  displayRow={
                    <>
                      <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-slate-700">{s.clave}</td>
                      <td className="whitespace-nowrap px-4 py-3"><RolBadge rol={s.rol} /></td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{s.descripcion}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                        {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(s.monto)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{s.vigencia_desde}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">{s.vigencia_hasta ?? '—'}</td>
                    </>
                  }
                  onSave={(v) => handleSavePlus(s.id, v)}
                  onDelete={() => handleDeletePlus(s.id)}
                  isDeleting={deletingPlusId === s.id}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
