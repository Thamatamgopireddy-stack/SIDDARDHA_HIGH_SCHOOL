import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense, useCallback } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './features/auth/AuthProvider'
import { useAuth } from './features/auth/useAuth'
import { AppShell } from './components/layout/AppShell'
import { SetupPage } from './features/auth/SetupPage'
import { LandingPage } from './features/auth/LandingPage'
import { RegistrationPage } from './features/auth/RegistrationPage'
import { AccountStatusPage } from './features/auth/AccountStatusPage'
import { OwnerBootstrapPage } from './features/auth/OwnerBootstrapPage'

const LoginPage = lazy(() => import('./features/auth/LoginPage').then((module) => ({ default: module.LoginPage })))
const DashboardPage = lazy(() => import('./features/dashboard/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const StudentsPage = lazy(() => import('./features/students/StudentsPage').then((module) => ({ default: module.StudentsPage })))
const StudentDetailPage = lazy(() => import('./features/students/StudentDetailPage').then((module) => ({ default: module.StudentDetailPage })))
const TeachersPage = lazy(() => import('./features/teachers/TeachersPage').then((module) => ({ default: module.TeachersPage })))
const AdmissionsPage = lazy(() => import('./features/admissions/AdmissionsPage').then((module) => ({ default: module.AdmissionsPage })))
const AttendancePage = lazy(() => import('./features/attendance/AttendancePage').then((module) => ({ default: module.AttendancePage })))
const ProfilePage = lazy(() => import('./features/auth/ProfilePage').then((module) => ({ default: module.ProfilePage })))
const UnauthorizedPage = lazy(() => import('./features/auth/AccountPages').then((module) => ({ default: module.UnauthorizedPage })))
const SuperAdminPage = lazy(() => import('./features/auth/SuperAdminPage').then((module) => ({ default: module.SuperAdminPage })))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
})

function ProtectedRoutes() {
  const { session, loading, configured, accountStatus, statusError } = useAuth()

  if (!configured) return <SetupPage />
  if (loading) {
    return (
      <main className="screen-center" aria-live="polite">
        <div className="spinner" />
        <span>Restoring your secure session…</span>
      </main>
    )
  }
  if (!session) return <Navigate to="/login" replace />
  if (statusError) {
    return <main className="screen-center"><div className="notice notice-error" role="alert">{statusError}</div></main>
  }
  if (!accountStatus || accountStatus.account_status !== 'approved' || !accountStatus.portal) {
    return <Navigate to="/account-status" replace />
  }

  return (
    <AppShell>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/students/:studentId" element={<StudentDetailPage />} />
          <Route path="/teachers" element={<TeachersPage />} />
          <Route path="/admissions" element={<AdmissionsPage />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          {accountStatus.portal === 'super_admin' && <Route path="/super-admin" element={<SuperAdminPage />} />}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </AppShell>
  )
}

function AppRoutes() {
  const { session, loading, configured, accountStatus } = useAuth()

  if (!configured) return <SetupPage />

  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route
          path="/"
          element={
            session
              ? loading
                ? <PageFallback />
                : <Navigate to={accountStatus?.account_status === 'approved' && accountStatus.portal ? '/dashboard' : '/account-status'} replace />
              : <LandingPage />
          }
        />
        <Route
          path="/login"
          element={
            session
              ? loading
                ? <PageFallback />
                : <Navigate to={accountStatus?.account_status === 'approved' && accountStatus.portal ? '/dashboard' : '/account-status'} replace />
              : <LoginPage />
          }
        />
        <Route path="/register/:role" element={<RegistrationPage />} />
        <Route path="/account-status" element={session ? <AccountStatusPage /> : <Navigate to="/login" replace />} />
        <Route path="/owner-bootstrap" element={<OwnerBootstrapPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route
          path="/*"
          element={
            loading ? (
              <main className="screen-center"><div className="spinner" />Restoring session…</main>
            ) : (
              <ProtectedRoutes />
            )
          }
        />
      </Routes>
    </Suspense>
  )
}

function App() {
  const clearPrivateCache = useCallback(() => queryClient.clear(), [])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider onSignOut={clearPrivateCache}>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function PageFallback() {
  return <main className="screen-center" aria-live="polite"><div className="spinner" />Loading page…</main>
}

export default App
