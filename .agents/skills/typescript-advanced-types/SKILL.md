---
name: typescript-advanced-types
description: Patrones TypeScript estrictos para active-trace. Sin any, tipos de API, Zod, React Hook Form, hooks custom tipados.
license: MIT
---

# TypeScript Advanced Types — active-trace

## Config base — strict mode

```json
// tsconfig.json — verificar que esté activo
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true
  }
}
```

## Tipos de respuestas de API

```typescript
// types/api.ts — tipos base reutilizables
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiError {
  detail: string | ValidationError[];
}

interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}
```

## Zod + inferencia de tipos

```typescript
// features/comunicaciones/types/index.ts
import { z } from "zod";

export const ComunicacionCreateSchema = z.object({
  asunto: z.string().min(1).max(255),
  cuerpo: z.string().min(1),
  destinatario_ids: z.array(z.string().uuid()).min(1).max(500),
});

// Inferir el tipo desde el schema — nunca duplicar
export type ComunicacionCreateDTO = z.infer<typeof ComunicacionCreateSchema>;

export const ComunicacionResponseSchema = z.object({
  id: z.string().uuid(),
  asunto: z.string(),
  estado: z.enum(["Pendiente", "Enviando", "Enviado", "Error", "Cancelado"]),
  created_at: z.string().datetime(),
});

export type ComunicacionResponse = z.infer<typeof ComunicacionResponseSchema>;
```

## React Hook Form + Zod

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

export function ComunicacionForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ComunicacionCreateDTO>({
    resolver: zodResolver(ComunicacionCreateSchema),
  });

  const onSubmit = async (data: ComunicacionCreateDTO) => {
    await comunicacionService.crear(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("asunto")} />
      {errors.asunto && <span>{errors.asunto.message}</span>}
    </form>
  );
}
```

## Custom hooks tipados

```typescript
// features/comunicaciones/hooks/useComunicaciones.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { ComunicacionResponse, ComunicacionCreateDTO } from "../types";

export function useComunicaciones() {
  return useQuery<ComunicacionResponse[]>({
    queryKey: ["comunicaciones"],
    queryFn: () => comunicacionService.listar(),
  });
}

export function useCrearComunicacion() {
  const qc = useQueryClient();
  return useMutation<ComunicacionResponse, Error, ComunicacionCreateDTO>({
    mutationFn: (data) => comunicacionService.crear(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["comunicaciones"] }),
  });
}
```

## Service layer tipado

```typescript
// features/comunicaciones/services/comunicacionService.ts
import { api } from "@/shared/services/api";
import type { ComunicacionResponse, ComunicacionCreateDTO } from "../types";

export const comunicacionService = {
  listar: (): Promise<ComunicacionResponse[]> =>
    api.get("/api/comunicaciones/").then((r) => r.data),

  crear: (data: ComunicacionCreateDTO): Promise<ComunicacionResponse> =>
    api.post("/api/comunicaciones/", data).then((r) => r.data),

  cancelar: (id: string): Promise<void> =>
    api.post(`/api/comunicaciones/${id}/cancelar`).then(() => undefined),
};
```

## Tipos de componentes — sin any

```typescript
// Props tipadas siempre
interface TablaAtrasadosProps {
  items: AlumnoAtrasado[];
  onSeleccionar: (ids: string[]) => void;
  isLoading?: boolean;
}

export function TablaAtrasados({
  items,
  onSeleccionar,
  isLoading = false,
}: TablaAtrasadosProps) {
  // ...
}

// Eventos tipados
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};

// Refs tipados
const inputRef = useRef<HTMLInputElement>(null);
```

## Discriminated unions para estados de UI

```typescript
type EstadoComunicacion =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ComunicacionResponse }
  | { status: "error"; error: string };

// Uso con type narrowing — sin as, sin !
function renderEstado(estado: EstadoComunicacion) {
  switch (estado.status) {
    case "success":
      return <span>{estado.data.asunto}</span>;  // TypeScript sabe que data existe
    case "error":
      return <span>{estado.error}</span>;
    default:
      return null;
  }
}
```

## Reglas

- **Sin `any`** — usar `unknown` y narrowing si el tipo es dinámico
- **Sin `as`** — si necesitás castear, hay un problema de diseño
- **Sin `!` (non-null assertion)** — usar optional chaining o guard
- **Tipos desde Zod** — `z.infer<typeof Schema>`, nunca duplicar interfaces manualmente
- **Props siempre tipadas** — nunca `(props: any)` ni `React.FC` sin genéricos
