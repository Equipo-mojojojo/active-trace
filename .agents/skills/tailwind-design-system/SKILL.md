---
name: tailwind-design-system
description: Patrones Tailwind CSS para active-trace. Componentes de UI, layouts, tablas, formularios, estados de carga y error.
license: MIT
---

# Tailwind Design System — active-trace

## Principios

- Sin CSS modules, sin inline styles (salvo valores dinámicos con template literal)
- Sin clases de colores hardcodeadas — usar las del sistema de diseño
- Componentes < 200 LOC — extraer componentes si el JSX crece

## Layout base de la aplicación

```tsx
// Shell principal — sidebar + content
export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
```

## Página con header + contenido

```tsx
export function PageLayout({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        {actions && <div className="flex gap-3">{actions}</div>}
      </div>
      {children}
    </div>
  );
}
```

## Tabla de datos

```tsx
export function DataTable<T>({
  columns,
  data,
  isLoading,
  emptyMessage = "No hay registros",
}: DataTableProps<T>) {
  if (isLoading) return <TableSkeleton />;

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-6 py-12 text-center text-sm text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                {columns.map((col) => (
                  <td key={col.key} className="px-6 py-4 text-sm text-gray-700">
                    {col.render ? col.render(row) : String(row[col.key as keyof T])}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
```

## Botones

```tsx
// Variantes de botón
const buttonVariants = {
  primary: "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500",
  secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-indigo-500",
  danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  ghost: "text-gray-600 hover:bg-gray-100 focus:ring-gray-400",
};

const baseButton = "inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors";

export function Button({
  variant = "primary",
  isLoading,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${baseButton} ${buttonVariants[variant]}`}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  );
}
```

## Formulario

```tsx
export function FormField({
  label,
  error,
  required,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}

// Input base
const inputBase = "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-50 disabled:text-gray-500";
```

## Estados de carga y error

```tsx
// Loading skeleton
export function TableSkeleton() {
  return (
    <div className="animate-pulse space-y-3 rounded-lg border border-gray-200 p-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-10 rounded bg-gray-200" />
      ))}
    </div>
  );
}

// Error state
export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <p className="text-sm font-medium text-red-800">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-sm text-red-700 underline">
          Reintentar
        </button>
      )}
    </div>
  );
}

// Empty state
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
      <p className="text-sm font-medium text-gray-900">{title}</p>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
```

## Badges de estado

```tsx
const estadoStyles: Record<string, string> = {
  Pendiente: "bg-yellow-100 text-yellow-800",
  Enviado:   "bg-green-100 text-green-800",
  Error:     "bg-red-100 text-red-800",
  Cancelado: "bg-gray-100 text-gray-600",
  Activo:    "bg-green-100 text-green-800",
  Inactivo:  "bg-gray-100 text-gray-600",
};

export function Badge({ estado }: { estado: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${estadoStyles[estado] ?? "bg-gray-100 text-gray-600"}`}>
      {estado}
    </span>
  );
}
```

## Modal

```tsx
export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
```
