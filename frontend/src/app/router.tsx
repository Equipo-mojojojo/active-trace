import { createBrowserRouter, Navigate } from 'react-router-dom'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { TwoFactorPage } from '@/features/auth/pages/TwoFactorPage'
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage'
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { AuthGuard } from '@/shared/components/guards/AuthGuard'
import { PermissionGuard } from '@/shared/components/guards/PermissionGuard'
import { AppLayout } from '@/shared/components/layout/AppLayout'
import { NotFoundPage } from '@/shared/components/ui/NotFoundPage'
import { ForbiddenPage } from '@/shared/components/ui/ForbiddenPage'
import { PublicRoute } from '@/shared/components/guards/PublicRoute'
import { MisAvisosPage } from '@/features/profesor/pages/MisAvisosPage'
import { MisComisionesPage } from '@/features/profesor/pages/MisComisionesPage'
import { ComisionPage } from '@/features/profesor/pages/ComisionPage'
import { ImportarCalificacionesPage } from '@/features/profesor/pages/ImportarCalificacionesPage'
import { ComunicacionPage } from '@/features/profesor/pages/ComunicacionPage'
import { TrackingComunicacionesPage } from '@/features/profesor/pages/TrackingComunicacionesPage'
import { MonitorDocentePage } from '@/features/monitor/pages/MonitorDocentePage'
// C-23 — Coordinación
// C-24 — Finanzas
import { LiquidacionesPage } from '@/features/finanzas/pages/LiquidacionesPage'
import { HistorialLiquidacionesPage } from '@/features/finanzas/pages/HistorialLiquidacionesPage'
import { GrillaSalarialPage } from '@/features/finanzas/pages/GrillaSalarialPage'
import { FacturasPage } from '@/features/finanzas/pages/FacturasPage'
// C-24 — Admin
import { EstructuraAcademicaPage } from '@/features/admin/pages/EstructuraAcademicaPage'
import { UsuariosPage } from '@/features/admin/pages/UsuariosPage'
import { AuditoriaPage } from '@/features/admin/pages/AuditoriaPage'
// C-23 — Coordinación
import { CoordinacionDashboardPage } from '@/features/coordinacion/pages/CoordinacionDashboardPage'
import { EquiposPage } from '@/features/coordinacion/pages/EquiposPage'
import { AvisosPage } from '@/features/coordinacion/pages/AvisosPage'
import { TareasPage } from '@/features/coordinacion/pages/TareasPage'
import { MonitorCoordinacionPage } from '@/features/coordinacion/pages/MonitorCoordinacionPage'
import { EncuentrosPage } from '@/features/encuentros/pages/EncuentrosPage'
import { GuardiasPage } from '@/features/encuentros/pages/GuardiasPage'
import { ColoquiosPage } from '@/features/coloquios/pages/ColoquiosPage'

/**
 * Application router.
 *
 * Route hierarchy:
 * - Public routes: /login, /auth/2fa, /auth/forgot-password, /auth/reset-password
 *   - If user is already authenticated → redirect to /dashboard (via PublicRoute)
 * - Protected routes (under AuthGuard + AppLayout):
 *   - /dashboard — placeholder; future feature modules add routes here
 *   - / → redirect to /dashboard
 * - Error routes: /403, * (404)
 */
export const router = createBrowserRouter([
  // ── Public routes (redirect to /dashboard if authenticated) ──────────────
  {
    element: <PublicRoute />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/auth/2fa', element: <TwoFactorPage /> },
      { path: '/auth/forgot-password', element: <ForgotPasswordPage /> },
      { path: '/auth/reset-password', element: <ResetPasswordPage /> },
    ],
  },

  // ── Protected routes (require authentication) ─────────────────────────────
  {
    element: <AuthGuard />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard', element: <DashboardPage /> },

          // ── Profesor — Avisos ──────────────────────────────────────────────
          {
            element: <PermissionGuard permission="aviso:ack" />,
            children: [
              { path: '/profesor/avisos', element: <MisAvisosPage /> },
            ],
          },

          // ── Profesor — Comisiones ──────────────────────────────────────────
          {
            element: <PermissionGuard permission={['atrasados:ver', 'atrasados:ver:propio']} />,
            children: [
              { path: '/profesor/comisiones', element: <MisComisionesPage /> },
              { path: '/profesor/comisiones/:comisionId', element: <ComisionPage /> },
              { path: '/monitor', element: <MonitorDocentePage /> },
            ],
          },

          // ── Profesor — Importar ────────────────────────────────────────────
          {
            element: <PermissionGuard permission={['calificaciones:importar', 'calificaciones:importar:propio']} />,
            children: [
              {
                path: '/profesor/comisiones/:comisionId/importar',
                element: <ImportarCalificacionesPage />,
              },
            ],
          },

          // ── Profesor — Comunicación ────────────────────────────────────────
          {
            element: <PermissionGuard permission={['comunicacion:enviar', 'comunicacion:enviar:propio']} />,
            children: [
              {
                path: '/profesor/comunicacion/tracking',
                element: <TrackingComunicacionesPage />,
              },
              {
                path: '/profesor/comunicacion/:comisionId',
                element: <ComunicacionPage />,
              },
            ],
          },

          // ── C-24 Finanzas — Liquidaciones ─────────────────────────────────
          {
            element: <PermissionGuard permission="liquidaciones:cerrar" />,
            children: [
              { path: '/finanzas/liquidaciones', element: <LiquidacionesPage /> },
              { path: '/finanzas/liquidaciones/historial', element: <HistorialLiquidacionesPage /> },
            ],
          },

          // ── C-24 Finanzas — Grilla salarial ───────────────────────────────
          {
            element: <PermissionGuard permission="liquidaciones:operar" />,
            children: [
              { path: '/finanzas/grilla-salarial', element: <GrillaSalarialPage /> },
            ],
          },

          // ── C-24 Finanzas — Facturas ───────────────────────────────────────
          {
            element: <PermissionGuard permission="facturas:gestionar" />,
            children: [
              { path: '/finanzas/facturas', element: <FacturasPage /> },
            ],
          },

          // ── C-24 Admin — Estructura académica ────────────────────────────
          {
            element: <PermissionGuard permission="estructura:gestionar" />,
            children: [
              { path: '/admin/estructura', element: <EstructuraAcademicaPage /> },
            ],
          },

          // ── C-24 Admin — Usuarios del tenant ─────────────────────────────
          {
            element: <PermissionGuard permission="usuarios:gestionar" />,
            children: [
              { path: '/admin/usuarios', element: <UsuariosPage /> },
            ],
          },

          // ── C-24 Admin — Auditoría (acepta ver o ver:propio) ─────────────
          // Note: auditoria:ver:propio has same route, backend restricts scope
          {
            element: <PermissionGuard permission="auditoria:ver" />,
            children: [
              { path: '/admin/auditoria', element: <AuditoriaPage /> },
            ],
          },

          // ── C-23 Coordinación — Módulo Equipos/Avisos/Tareas/Monitor ────
          {
            element: <PermissionGuard permission="equipos:asignar" />,
            children: [
              { path: '/coordinacion', element: <CoordinacionDashboardPage /> },
              { path: '/coordinacion/equipos', element: <EquiposPage /> },
            ],
          },
          {
            element: <PermissionGuard permission="avisos:publicar" />,
            children: [
              { path: '/coordinacion/avisos', element: <AvisosPage /> },
            ],
          },
          {
            element: <PermissionGuard permission={['tareas:gestionar', 'tareas:gestionar:propio']} />,
            children: [
              { path: '/coordinacion/tareas', element: <TareasPage /> },
            ],
          },
          {
            element: <PermissionGuard permission="atrasados:ver" />,
            children: [
              { path: '/coordinacion/monitor', element: <MonitorCoordinacionPage /> },
            ],
          },

          // ── C-23 Coordinación — Encuentros y Guardias ────────────────────
          {
            element: <PermissionGuard permission={['encuentros:gestionar', 'encuentros:gestionar:propio']} />,
            children: [
              { path: '/encuentros', element: <EncuentrosPage /> },
              { path: '/encuentros/guardias', element: <GuardiasPage /> },
            ],
          },

          // ── C-23 Coordinación — Coloquios ─────────────────────────────────
          {
            element: <PermissionGuard permission="equipos:asignar" />,
            children: [
              { path: '/coloquios', element: <ColoquiosPage /> },
            ],
          },
        ],
      },
    ],
  },

  // ── Error routes ──────────────────────────────────────────────────────────
  { path: '/403', element: <ForbiddenPage /> },
  { path: '*', element: <NotFoundPage /> },
])
