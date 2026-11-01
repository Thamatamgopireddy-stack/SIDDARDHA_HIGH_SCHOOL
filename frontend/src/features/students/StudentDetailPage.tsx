import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Archive, CalendarDays, Pencil, Save, UserRound } from 'lucide-react'
import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'
import { ErrorState, LoadingState, Toast } from '../../components/common/Feedback'
import { Modal } from '../../components/common/Modal'
import { StatusBadge } from '../../components/common/StatusBadge'
import { deleteData, getApiError, getData, patchData } from '../../lib/api'
import type { AttendanceRecord, Student } from '../../lib/types'
import { usePermissions } from '../../hooks/usePermissions'

const editSchema = z.object({
  first_name: z.string().trim().min(1, 'First name is required').max(100),
  last_name: z.string().trim().min(1, 'Last name is required').max(100),
  class_name: z.string().trim().min(1, 'Class is required').max(32),
  section: z.string().trim().min(1, 'Section is required').max(32),
  roll_number: z.string().trim().min(1, 'Roll number is required').max(32),
  status: z.enum(['active', 'inactive', 'graduated', 'transferred']),
})
type EditValues = z.infer<typeof editSchema>

export function StudentDetailPage() {
  const { studentId = '' } = useParams()
  const navigate = useNavigate()
  const client = useQueryClient()
  const [editOpen, setEditOpen] = useState(false)
  const [archiveOpen, setArchiveOpen] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [feedbackError, setFeedbackError] = useState(false)
  const permissions = usePermissions()
  const canReadAttendance = permissions.data?.includes('attendance:read') ?? false
  const student = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => getData<Student>(`/students/${studentId}`),
    enabled: Boolean(studentId && canReadAttendance),
  })
  const attendance = useQuery({
    queryKey: ['student', studentId, 'attendance'],
    queryFn: () => getData<AttendanceRecord[]>(`/attendance/student/${studentId}`),
    enabled: Boolean(studentId),
  })
  const form = useForm<EditValues>({ resolver: zodResolver(editSchema) })
  const update = useMutation({
    mutationFn: (values: EditValues) => patchData<Student, EditValues>(`/students/${studentId}`, values),
    onSuccess: async (value) => {
      client.setQueryData(['student', studentId], value)
      await client.invalidateQueries({ queryKey: ['students'] })
      setEditOpen(false)
      setFeedback('Student record updated.')
      setFeedbackError(false)
    },
  })
  const archive = useMutation({
    mutationFn: () => deleteData<Student>(`/students/${studentId}`),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['students'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      navigate('/students', { replace: true })
    },
  })

  useEffect(() => {
    if (student.data) form.reset({
      first_name: student.data.first_name,
      last_name: student.data.last_name,
      class_name: student.data.class_name,
      section: student.data.section,
      roll_number: student.data.roll_number,
      status: student.data.status,
    })
  }, [student.data, form])

  if (student.isLoading) return <LoadingState label="Loading student profile…" />
  if (student.error || !student.data) return <ErrorState error={student.error ?? new Error('Student not found')} onRetry={() => void student.refetch()} />
  const record = student.data
  const fullName = `${record.first_name} ${record.last_name}`

  return (
    <>
      <div className="page-heading">
        <div><Link className="inline-meta table-link" style={{ gap: 6, fontSize: 11 }} to="/students"><ArrowLeft size={14} /> Back to students</Link><h1>{fullName}</h1><p className="subtitle">Student record · {record.admission_number}</p></div>
        <div className="heading-actions">
          <button className="button" onClick={() => setEditOpen(true)} type="button"><Pencil size={15} /> Edit</button>
          <button className="button button-danger" onClick={() => setArchiveOpen(true)} type="button"><Archive size={15} /> Archive</button>
        </div>
      </div>
      {update.error && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(update.error)}</div>}
      <section className="grid student-detail-grid">
        <article className="card">
          <div className="card-header"><div><div className="card-title">Student information</div><div className="card-subtitle">Current school record</div></div><UserRound size={17} color="#8290a4" /></div>
          <div className="card-body">
            <div className="detail-list">
              <Detail label="Full name" value={fullName} />
              <Detail label="Admission number" value={record.admission_number} />
              <Detail label="Class and section" value={`${record.class_name} · ${record.section}`} />
              <Detail label="Roll number" value={record.roll_number} />
              <Detail label="Date of birth" value={record.date_of_birth ? new Date(`${record.date_of_birth}T00:00:00`).toLocaleDateString() : 'Not provided'} />
              <div className="detail-item"><div className="meta-label">Record status</div><div style={{ marginTop: 6 }}><StatusBadge value={record.status} /></div></div>
            </div>
          </div>
        </article>
        <article className="card">
          <div className="card-header"><div><div className="card-title">Attendance history</div><div className="card-subtitle">Recent records for this student</div></div><CalendarDays size={17} color="#8290a4" /></div>
          {!canReadAttendance ? <div className="card-body"><div className="empty-state">Attendance history is not available for your account.</div></div> : attendance.isLoading ? <LoadingState /> : attendance.error ? <ErrorState error={attendance.error} onRetry={() => void attendance.refetch()} /> : (attendance.data?.length ?? 0) === 0 ? <div className="card-body"><div className="empty-state">No attendance records yet.</div></div> : (
            <div className="table-wrap"><table><thead><tr><th>Date</th><th>Session</th><th>Status</th></tr></thead><tbody>
              {attendance.data?.slice(0, 10).map((entry) => <tr key={entry.id}><td>{new Date(`${entry.attendance_date}T00:00:00`).toLocaleDateString()}</td><td>{entry.session.replace(/_/g, ' ')}</td><td><StatusBadge value={entry.status} /></td></tr>)}
            </tbody></table></div>
          )}
        </article>
      </section>
      {feedback && <Toast message={feedback} error={feedbackError} />}
      {editOpen && <Modal
        title="Edit student record"
        description="Changes are saved to the school database."
        onClose={() => setEditOpen(false)}
        footer={<><button className="button" onClick={() => setEditOpen(false)} type="button">Cancel</button><button className="button button-primary" disabled={update.isPending} form="student-edit-form" type="submit"><Save size={14} /> Save changes</button></>}
      >
        <form className="form-grid" id="student-edit-form" onSubmit={(event) => void form.handleSubmit((values) => update.mutate(values))(event)}>
          <FormField id="edit-first" label="First name" error={form.formState.errors.first_name?.message}><input className="field-input" id="edit-first" {...form.register('first_name')} /></FormField>
          <FormField id="edit-last" label="Last name" error={form.formState.errors.last_name?.message}><input className="field-input" id="edit-last" {...form.register('last_name')} /></FormField>
          <FormField id="edit-class" label="Class" error={form.formState.errors.class_name?.message}><input className="field-input" id="edit-class" {...form.register('class_name')} /></FormField>
          <FormField id="edit-section" label="Section" error={form.formState.errors.section?.message}><input className="field-input" id="edit-section" {...form.register('section')} /></FormField>
          <FormField id="edit-roll" label="Roll number" error={form.formState.errors.roll_number?.message}><input className="field-input" id="edit-roll" {...form.register('roll_number')} /></FormField>
          <FormField id="edit-status" label="Status"><select className="field-select" id="edit-status" {...form.register('status')}><option value="active">Active</option><option value="inactive">Inactive</option><option value="graduated">Graduated</option><option value="transferred">Transferred</option></select></FormField>
        </form>
      </Modal>}
      {archiveOpen && <Modal
        title="Archive student?"
        description={`${fullName} will be marked inactive. Their record will remain in the database.`}
        onClose={() => setArchiveOpen(false)}
        footer={<><button className="button" onClick={() => setArchiveOpen(false)} type="button">Cancel</button><button className="button button-danger" disabled={archive.isPending} onClick={() => archive.mutate()} type="button">{archive.isPending ? 'Archiving…' : 'Archive student'}</button></>}
      >
        {archive.error && <div className="notice notice-error" role="alert">{getApiError(archive.error)}</div>}
      </Modal>}
    </>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail-item"><div className="meta-label">{label}</div><div className="detail-value">{value}</div></div>
}

function FormField({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return <div className="form-field"><label className="field-label" htmlFor={id}>{label}</label>{children}{error && <div className="field-error">{error}</div>}</div>
}
