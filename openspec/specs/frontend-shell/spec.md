## ADDED Requirements

### Requirement: SPA scaffold con estructura feature-based
El sistema SHALL proveer una SPA React 18 + TypeScript construida con Vite, organizada en módulos de negocio bajo `src/features/`. Las dependencias de base (TanStack Query, React Router, Tailwind, Axios, Zod) deben estar configuradas y operativas desde el inicio.

#### Scenario: App levanta sin errores
- **WHEN** se ejecuta `npm run dev` en el directorio `frontend/`
- **THEN** Vite sirve la app en `http://localhost:5173` sin errores de compilación ni en consola

#### Scenario: TypeScript strict activo
- **WHEN** se ejecuta `npx tsc --noEmit`
- **THEN** no hay errores de tipo (strict mode habilitado en tsconfig)

#### Scenario: Tailwind con design tokens cargados
- **WHEN** un componente usa `className="bg-primary-600 text-white"`
- **THEN** el color se aplica con el valor definido en `tailwind.config.ts` (no el default de Tailwind)

### Requirement: Cliente HTTP centralizado con interceptor de auth
El sistema SHALL proveer una instancia Axios configurada en `src/shared/services/api.ts` que inyecte automáticamente el Authorization header en cada request y gestione el refresh transparente del access token.

#### Scenario: Access token inyectado automáticamente
- **WHEN** cualquier componente llama a `api.get('/api/alumnos/')`
- **THEN** el request incluye `Authorization: Bearer <token>` sin que el componente lo maneje explícitamente

#### Scenario: Refresh transparente ante 401
- **WHEN** el backend responde 401 (token expirado)
- **THEN** el interceptor ejecuta `POST /auth/refresh`, obtiene un nuevo access token y reintenta el request original de forma transparente, sin que el componente ni el hook lo note

#### Scenario: Cola de reintentos durante refresh simultáneo
- **WHEN** llegan 3 requests simultáneos con 401 mientras ya hay un refresh en curso
- **THEN** solo se ejecuta 1 llamada a `/auth/refresh` y los 3 requests se reintentan con el token nuevo

#### Scenario: Logout ante refresh fallido
- **WHEN** el refresh token también expiró o fue revocado (el backend devuelve 401 en `/auth/refresh`)
- **THEN** el interceptor limpia la sesión y redirige a `/login`

### Requirement: Providers raíz configurados
El sistema SHALL montar `QueryClientProvider`, `AuthProvider` y `RouterProvider` en el componente raíz para que toda la app tenga acceso a TanStack Query, el estado de sesión y el router.

#### Scenario: TanStack Query disponible en cualquier componente
- **WHEN** un componente usa `useQuery` en cualquier feature
- **THEN** funciona correctamente sin configuración adicional (el provider ya está en el árbol)

#### Scenario: Auth context disponible en cualquier componente
- **WHEN** un componente llama a `useAuth()`
- **THEN** recibe `{ user, roles, permissions, tenant, isAuthenticated }` correctamente poblados
