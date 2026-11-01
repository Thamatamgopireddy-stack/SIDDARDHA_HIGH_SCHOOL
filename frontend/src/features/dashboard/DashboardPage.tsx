import { useQuery } from '@tanstack/react-query'
import { Activity, ArrowRight, BookOpenCheck, ClipboardCheck, GraduationCap, UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../../components/common/Feedback'
import { api, getData } from '../../lib/api'
import type { Admission, Page, Student, SuccessEnvelope, Teacher } from '../../lib/types'
import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const permissions = useQuery({
    queryKey: ['permissions'],
    queryFn: async () => (await api.get<SuccessEnvelope<string[]>>('/auth/permissions')).data.data,
  })
  const granted = new Set(permissions.data ?? [])
  const students = useQuery({
    queryKey: ['dashboard', 'students'],
    enabled: granted.has('students:read'),
    queryFn: () => getData<Page<Student>>('/students', { params: { page: 1, page_size: 1 } }),
  })
  const teachers = useQuery({
    queryKey: ['dashboard', 'teachers'],
    enabled: granted.has('teachers:read'),
    queryFn: () => getData<Page<Teacher>>('/teachers', { params: { page: 1, page_size: 1 } }),
  })
  const admissions = useQuery({
    queryKey: ['dashboard', 'admissions'],
    enabled: granted.has('admissions:read'),
    queryFn: () => getData<Page<Admission>>('/admissions', { params: { page: 1, page_size: 1 } }),
  })
  const attendance = useQuery({
    queryKey: ['dashboard', 'attendance', today()],
    enabled: granted.has('attendance:read'),
    queryFn: () => getData<Record<string, number>>('/attendance/summary', { params: { date: today() } }),
  })
  const liveness = useQuery({
    queryKey: ['backend', 'liveness'],
    queryFn: () => api.get<SuccessEnvelope<{ status: string }>>('/health'),
  })
  const readiness = useQuery({
    queryKey: ['backend', 'readiness'],
    queryFn: () => api.get<SuccessEnvelope<{ status: string }>>('/health/ready'),
    retry: false,
  })
  const { session } = useAuth()
  const pending = [permissions, students, teachers, admissions, attendance].some((query) => query.isLoading)
  const loadError = permissions.error ?? students.error ?? teachers.error ?? admissions.error ?? attendance.error
  const attendanceTotal = attendance.data ? Object.values(attendance.data).reduce((sum, value) => sum + value, 0) : 0
  const presentRate = attendanceTotal
    ? Math.round(((attendance.data?.present ?? 0) / attendanceTotal) * 100)
    : null

  if (pending) return <LoadingState label="Loading your school overview…" />
  if (loadError) return <ErrorState error={loadError} onRetry={() => void permissions.refetch()} />

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">School operations</div><h1>Good to see you</h1><p className="subtitle">Your school workspace at a glance.</p></div>
        <div className="heading-actions"><span className="badge badge-active">Signed in securely</span></div>
      </div>
      <section aria-label="School statistics" className="grid stats-grid">
        <StatCard label="Students" value={students.data?.total} note={granted.has('students:read') ? 'Records in your school' : 'Not available for this account'} icon={<GraduationCap size={17} />} />
        <StatCard label="Teachers" value={teachers.data?.total} note={granted.has('teachers:read') ? 'Records in your school' : 'Not available for this account'} icon={<UsersRound size={17} />} />
        <StatCard label="Admission applications" value={admissions.data?.total} note={granted.has('admissions:read') ? 'Applications on file' : 'Not available for this account'} icon={<BookOpenCheck size={17} />} />
        <StatCard label="Present today" value={attendance.data?.present} note={presentRate === null ? 'No attendance recorded today' : `${presentRate}% of recorded attendance`} icon={<ClipboardCheck size={17} />} />
      </section>
      <section className="grid dashboard-grid">
        <article className="card">
          <div className="card-header"><div><div className="card-title">Your workspace</div><div className="card-subtitle">Available, connected backend workflows</div></div><Activity size={17} color="#8290a4" /></div>
          <div className="card-body">
            <WorkspaceRow to="/students" title="Student records" count={students.data?.total} available={granted.has('students:read')} />
            <WorkspaceRow to="/teachers" title="Teacher directory" count={teachers.data?.total} available={granted.has('teachers:read')} />
            <WorkspaceRow to="/admissions" title="Admissions" count={admissions.data?.total} available={granted.has('admissions:read')} />
            <WorkspaceRow to="/attendance" title="Attendance" count={attendanceTotal} available={granted.has('attendance:read')} />
          </div>
        </article>
        <article className="card">
          <div className="card-header"><div><div className="card-title">System status</div><div className="card-subtitle">Live connectivity checks</div></div><Activity size={17} color="#8290a4" /></div>
          <div className="card-body">
            <HealthRow name="Backend API" healthy={liveness.isSuccess} pending={liveness.isLoading} />
            <HealthRow name="Database" healthy={readiness.data?.data.data.status === 'ready'} pending={readiness.isLoading} error={readiness.isError} />
            <div className="dashboard-note" style={{ marginTop: 16 }}>
              <Activity size={16} />
              <span>Metrics above are fetched from the connected API. Access is determined by backend permissions, not this interface.</span>
            </div>
          </div>
        </article>
      </section>
      <div className="footer-note">Session: {session?.user.email ?? 'Authenticated school account'} · School records are protected by your account permissions.</div>
    </>
  )
}

function StatCard({ label, value, note, icon }: { label: string; value?: number; note: string; icon: import('react').ReactNode }) {
  return <article className="card stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div><div className="stat-value">{value === undefined ? '—' : value.toLocaleString()}</div><div className="stat-note">{note}</div></article>
}

function WorkspaceRow({ to, title, count, available }: { to: string; title: string; count?: number; available: boolean }) {
  return (
    <div className="health-row">
      <span className="health-name">{title}</span>
      {available ? <Link className="table-link inline-meta" to={to}>{count ?? '—'} records <ArrowRight size={14} style={{ marginLeft: 5 }} /></Link> : <span className="health-state" style={{ color: '#929daf' }}>No permission</span>}
    </div>
  )
}

function HealthRow({ name, healthy, pending, error = false }: { name: string; healthy: boolean; pending: boolean; error?: boolean }) {
  const text = pending ? 'Checking' : error ? 'Unavailable' : healthy ? 'Connected' : 'Unavailable'
  return <div className="health-row"><span className="health-name">{name}</span><span className="health-state" style={{ color: healthy ? undefined : '#a36a14' }}><span className={`dot${healthy ? '' : ' dot-muted'}`} />{text}</span></div>
}

function today() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
