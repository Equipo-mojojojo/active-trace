import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { comisionesService } from '../services/comisionesService'
import type { ActividadDetectada } from '../types/profesor.types'

type ImportStep = 'upload' | 'preview' | 'confirmar'

interface ImportState {
  step: ImportStep
  file: File | null
  actividadesDetectadas: ActividadDetectada[]
  seleccionadas: string[]
  error: string | null
}

export function useImportarCalificaciones(materiaId: string) {
  const queryClient = useQueryClient()

  const [state, setState] = useState<ImportState>({
    step: 'upload',
    file: null,
    actividadesDetectadas: [],
    seleccionadas: [],
    error: null,
  })

  const previewMutation = useMutation({
    mutationFn: (file: File) => comisionesService.previewCalificaciones(materiaId, file),
    onSuccess: (data, file) => {
      setState((prev) => ({
        ...prev,
        step: 'preview',
        file,
        actividadesDetectadas: data.actividades,
        seleccionadas: data.actividades.map((a) => a.nombre),
        error: null,
      }))
    },
    onError: (err: Error) => {
      setState((prev) => ({ ...prev, error: err.message }))
    },
  })

  const importMutation = useMutation({
    mutationFn: () => {
      if (!state.file) throw new Error('No file selected')
      return comisionesService.importarCalificaciones(
        materiaId,
        state.file,
        state.seleccionadas,
      )
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['atrasados', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['ranking', materiaId] })
      void queryClient.invalidateQueries({ queryKey: ['notas-finales', materiaId] })
      setState((prev) => ({ ...prev, step: 'confirmar', error: null }))
    },
    onError: (err: Error) => {
      setState((prev) => ({ ...prev, error: err.message }))
    },
  })

  const toggleActividad = (nombre: string) => {
    setState((prev) => ({
      ...prev,
      seleccionadas: prev.seleccionadas.includes(nombre)
        ? prev.seleccionadas.filter((a) => a !== nombre)
        : [...prev.seleccionadas, nombre],
    }))
  }

  const goBack = () => {
    setState((prev) => ({
      ...prev,
      step: prev.step === 'preview' ? 'upload' : 'preview',
      error: null,
    }))
  }

  return {
    ...state,
    isUploading: previewMutation.isPending,
    isImporting: importMutation.isPending,
    uploadFile: (file: File) => previewMutation.mutate(file),
    confirmar: () => importMutation.mutate(),
    toggleActividad,
    goBack,
  }
}
