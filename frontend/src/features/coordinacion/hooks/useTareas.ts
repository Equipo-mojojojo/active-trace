import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tareasService, type TareaTab } from '../services/tareasService'
import type { Tarea, TareaCreate, ComentarioTarea } from '../types/coordinacion.types'

export const tareaQueryKeys = {
  tareas: (tab: TareaTab) => ['tareas', tab] as const,
  tarea: (id: string) => ['tareas', 'detail', id] as const,
  comentariosTarea: (tareaId: string) => ['tareas', tareaId, 'comentarios'] as const,
}

export function useTareas(tab: TareaTab) {
  return useQuery<Tarea[]>({
    queryKey: tareaQueryKeys.tareas(tab),
    queryFn: () => tareasService.getTareas(tab),
  })
}

export function useTarea(id: string) {
  return useQuery<Tarea>({
    queryKey: tareaQueryKeys.tarea(id),
    queryFn: () => tareasService.getTarea(id),
    enabled: Boolean(id),
  })
}

export function useComentariosTarea(tareaId: string) {
  return useQuery<ComentarioTarea[]>({
    queryKey: tareaQueryKeys.comentariosTarea(tareaId),
    queryFn: () => tareasService.getComentarios(tareaId),
    enabled: Boolean(tareaId),
  })
}

export function useCreateTarea() {
  const queryClient = useQueryClient()
  return useMutation<Tarea, Error, TareaCreate>({
    mutationFn: (payload) => tareasService.createTarea(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] })
    },
  })
}

export function useUpdateEstadoTarea() {
  const queryClient = useQueryClient()
  return useMutation<Tarea, Error, { id: string; estado: string }>({
    mutationFn: ({ id, estado }) => tareasService.updateEstadoTarea(id, estado),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] })
      queryClient.invalidateQueries({ queryKey: tareaQueryKeys.tarea(id) })
    },
  })
}

export function useAddComentario() {
  const queryClient = useQueryClient()
  return useMutation<ComentarioTarea, Error, { tareaId: string; texto: string }>({
    mutationFn: ({ tareaId, texto }) => tareasService.addComentario(tareaId, texto),
    onSuccess: (_data, { tareaId }) => {
      queryClient.invalidateQueries({ queryKey: tareaQueryKeys.comentariosTarea(tareaId) })
    },
  })
}
