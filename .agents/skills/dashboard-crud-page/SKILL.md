---
name: dashboard-crud-page
description: >
  Estandariza páginas CRUD en active-trace con estructura consistente, TanStack Query, React Hook Form + Zod, modales y paginación.
  Trigger: Al crear cualquier página CRUD en features/{nombre}/{pages,components}/
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "2.0-active-trace"
---

## Cuándo usar

- Crear una nueva página con tabla + formulario (crear/editar) + confirmación de eliminación
- Cualquier módulo que gestione un recurso con listado paginado y ABM

---

## Stack obligatorio

| Necesidad | Herramienta |
|-----------|-------------|
| Server state (fetch, mutaciones) | **TanStack Query** (`useQuery`, `useMutation`) |
| Formularios | **React Hook Form + Zod** (`useForm`, `zodResolver`) |
| Estado de modales | `useState` local (simple, no global) |
| HTTP | Axios via `@/shared/services/api` |

---

## Estructura obligatoria de la página

```
// Orden de hooks — NUNCA condicional
useQuery (listado)
useState → isCreateOpen, isEditOpen, itemToEdit, itemToDelete
useMutation (crear, editar, eliminar) + onSuccess → invalidateQueries
useForm (React Hook Form + Zod)
handlers: openCreate, openEdit, openDelete, onSubmit, onConfirmDelete

// JSX
<PageLayout title="..." actions={<Button onClick={openCreate}>Nuevo</Button>}>
  {isLoading ? <TableSkeleton /> : (
    <DataTable columns={columns} data={items ?? []} />
  )}
  <Pagination ... />

  {/* Modal crear/editar */}
  <Modal isOpen={isCreateOpen || isEditOpen} onClose={closeModal} title="...">
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <FormField label="..." error={errors.campo?.message}>
        <input {...register("campo")} />
      </FormField>
      <div className="flex justify-end gap-3">
        <Button variant="secondary" onClick={closeModal}>Cancelar</Button>
        <Button type="submit" isLoading={isMutating}>Guardar</Button>
      </div>
    </form>
  </Modal>

  {/* Confirm delete */}
  <ConfirmDialog
    isOpen={!!itemToDelete}
    onClose={() => setItemToDelete(null)}
    onConfirm={onConfirmDelete}
    title="Eliminar ..."
    message={`¿Eliminar "${itemToDelete?.nombre}"?`}
    isLoading={isDeleting}
  />
</PageLayout>
```

---

## Patrón completo de página CRUD

```typescript
// features/tareas/pages/TareasPage.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { TareaSchema, type TareaFormDTO } from "../types";
import { tareaService } from "../services/tareaService";
import { PageLayout, DataTable, TableSkeleton, Modal, ConfirmDialog, FormField, Button, Badge } from "@/shared/ui";
import type { TareaResponse } from "../types";

export function TareasPage() {
  const qc = useQueryClient();

  // Server state
  const { data: tareas, isLoading } = useQuery({
    queryKey: ["tareas"],
    queryFn: tareaService.listar,
  });

  // Modal state — simple useState local
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [itemToEdit, setItemToEdit] = useState<TareaResponse | null>(null);
  const [itemToDelete, setItemToDelete] = useState<TareaResponse | null>(null);

  // Mutations
  const { mutate: crear, isPending: isCreating } = useMutation({
    mutationFn: tareaService.crear,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tareas"] });
      toast.success("Tarea creada");
      closeForm();
    },
    onError: () => toast.error("Error al crear la tarea"),
  });

  const { mutate: editar, isPending: isEditing } = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TareaFormDTO }) =>
      tareaService.editar(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tareas"] });
      toast.success("Tarea actualizada");
      closeForm();
    },
    onError: () => toast.error("Error al actualizar"),
  });

  const { mutate: eliminar, isPending: isDeleting } = useMutation({
    mutationFn: tareaService.eliminar,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tareas"] });
      toast.success("Tarea eliminada");
      setItemToDelete(null);
    },
    onError: () => toast.error("Error al eliminar"),
  });

  // Form
  const { register, handleSubmit, reset, formState: { errors } } = useForm<TareaFormDTO>({
    resolver: zodResolver(TareaSchema),
  });

  // Handlers
  const openCreate = () => {
    reset({});
    setItemToEdit(null);
    setIsFormOpen(true);
  };

  const openEdit = (item: TareaResponse) => {
    reset({ titulo: item.titulo, descripcion: item.descripcion });
    setItemToEdit(item);
    setIsFormOpen(true);
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setItemToEdit(null);
    reset({});
  };

  const onSubmit = (data: TareaFormDTO) => {
    if (itemToEdit) {
      editar({ id: itemToEdit.id, data });
    } else {
      crear(data);
    }
  };

  const onConfirmDelete = () => {
    if (itemToDelete) eliminar(itemToDelete.id);
  };

  // Columns
  const columns = [
    {
      key: "titulo",
      label: "Título",
      render: (item: TareaResponse) => (
        <span className="font-medium text-slate-900">{item.titulo}</span>
      ),
    },
    {
      key: "estado",
      label: "Estado",
      render: (item: TareaResponse) => <Badge estado={item.estado} />,
    },
    {
      key: "actions",
      label: "",
      render: (item: TareaResponse) => (
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => openEdit(item)}>
            Editar
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setItemToDelete(item)}
            className="text-red-600 hover:text-red-700"
          >
            Eliminar
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageLayout
      title="Tareas"
      actions={<Button onClick={openCreate}>Nueva tarea</Button>}
    >
      {isLoading ? (
        <TableSkeleton />
      ) : (
        <DataTable columns={columns} data={tareas ?? []} />
      )}

      <Modal
        isOpen={isFormOpen}
        onClose={closeForm}
        title={itemToEdit ? "Editar tarea" : "Nueva tarea"}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <FormField label="Título" required error={errors.titulo?.message}>
            <input
              {...register("titulo")}
              className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </FormField>
          <FormField label="Descripción" error={errors.descripcion?.message}>
            <textarea
              {...register("descripcion")}
              rows={3}
              className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </FormField>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeForm}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isCreating || isEditing}>
              {itemToEdit ? "Guardar" : "Crear"}
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!itemToDelete}
        onClose={() => setItemToDelete(null)}
        onConfirm={onConfirmDelete}
        title="Eliminar tarea"
        message={`¿Eliminás "${itemToDelete?.titulo}"? Esta acción no se puede deshacer.`}
        isLoading={isDeleting}
      />
    </PageLayout>
  );
}
```

---

## Tipos y schema Zod

```typescript
// features/tareas/types/index.ts
import { z } from "zod";

export const TareaSchema = z.object({
  titulo: z.string().min(1, "El título es requerido").max(255),
  descripcion: z.string().optional(),
});

export type TareaFormDTO = z.infer<typeof TareaSchema>;

export interface TareaResponse {
  id: string;
  titulo: string;
  descripcion: string | null;
  estado: "Pendiente" | "En progreso" | "Resuelta" | "Cancelada";
  created_at: string;
}
```

---

## Service layer

```typescript
// features/tareas/services/tareaService.ts
import { api } from "@/shared/services/api";
import type { TareaResponse, TareaFormDTO } from "../types";

export const tareaService = {
  listar: (): Promise<TareaResponse[]> =>
    api.get("/api/tareas/").then((r) => r.data),

  crear: (data: TareaFormDTO): Promise<TareaResponse> =>
    api.post("/api/tareas/", data).then((r) => r.data),

  editar: (id: string, data: TareaFormDTO): Promise<TareaResponse> =>
    api.put(`/api/tareas/${id}`, data).then((r) => r.data),

  eliminar: (id: string): Promise<void> =>
    api.delete(`/api/tareas/${id}`).then(() => undefined),
};
```

---

## ConfirmDialog component

```typescript
// shared/ui/ConfirmDialog.tsx
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  isLoading?: boolean;
  confirmLabel?: string;
}

export function ConfirmDialog({
  isOpen, onClose, onConfirm, title, message, isLoading, confirmLabel = "Eliminar",
}: ConfirmDialogProps) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-sm text-slate-600">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancelar
          </Button>
          <Button
            onClick={onConfirm}
            isLoading={isLoading}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

## Checklist antes de entregar una página CRUD

- [ ] `useQuery` para el listado — nunca `useState` + `useEffect` para fetch
- [ ] `useMutation` para crear/editar/eliminar con `onSuccess → invalidateQueries`
- [ ] `useForm` con `zodResolver` — nunca `useState` para campos de formulario
- [ ] Schema Zod en `types/index.ts` — tipos inferidos con `z.infer<>`
- [ ] `<TableSkeleton />` mientras `isLoading`
- [ ] `reset({...})` al abrir modal de edición con datos del item
- [ ] `reset({})` al cerrar el modal
- [ ] Toast en español (`toast.success / toast.error`)
- [ ] `isPending` del mutation en el botón de submit (`isLoading={isPending}`)
- [ ] Soft delete — el backend marca `deleted_at`, el frontend llama al endpoint DELETE
- [ ] `aria-label` en botones icon-only
- [ ] Columnas tipadas con el tipo de respuesta del backend
- [ ] Service layer en `services/` — nunca llamadas Axios directo en el componente
