import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Check, ClipboardCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import { ErrorState, LoadingState, Toast } from '../../components/common/Feedback'
import { StatusBadge } from '../../components/common/StatusBadge'
import { getApiError, getData, postData } from '../../lib/api'
import type { AttendanceRecord, Page, Student } from '../../lib/types'
import { usePermissions } from '../../hooks/usePermissions'

type AttendanceStatus = AttendanceRecord['status']

export function AttendancePage() {
  const [className, setClassName] = useState('')
  const [section, setSection] = useState('')
  const [attendanceDate, setAttendanceDate] = useState(today())
  const [statuses, setStatuses] = useState<Record<string, AttendanceStatus>>({})
  const [toast, setToast] = useState('')
  const client = useQueryClient()
  const permissions = usePermissions()
  const canWrite = permissions.data?.includes('attendance:write') ?? false
  const canRead = permissions.data?.includes('attendance:read') ?? false
  const canReadStudents = permissions.data?.includes('students:read') ?? false
  const summary = useQuery({
    queryKey: ['attendance-summary', attendanceDate],
    queryFn: () => getData<Record<string, number>>('/attendance/summary', { params: { date: attendanceDate } }),
    enabled: canRead,
  })
  const students = useQuery({
    queryKey: ['attendance-register', className, section],
    queryFn: async () => {
      const first = await getData<Page<Student>>('/students', { params: { page: 1, page_size: 100, class_name: className, section } })
      const all = [...first.items]
      if (first.total > 500) throw new Error('This register has more than 500 students. The current bulk attendance endpoint allows up to 500 records per request.')
      for (let page = 2; page <= first.total_pages; page += 1) {
        const next = await getData<Page<Student>>('/students', { params: { page, page_size: 100, class_name: className, section } })
        all.push(...next.items)
      }
      return all.filter((student) => student.status === 'active')
    },
    enabled: Boolean(className.trim() && section.trim() && canReadStudents),
  })
  const history = useQuery({
    queryKey: ['attendance-history', className, section, attendanceDate],
    queryFn: async () => {
      if (!students.data) return []
      const results: AttendanceRecord[] = []
      for (let start = 0; start < students.data.length; start += 10) {
        const group = students.data.slice(start, start + 10)
        const data = await Promise.all(group.map((student) => getData<AttendanceRecord[]>(`/attendance/student/${student.id}`, {
          params: { start_date: attendanceDate, end_date: attendanceDate },
        })))
        results.push(...data.flat())
      }
      return results
    },
    enabled: canRead && Boolean(students.data?.length),
  })
  const recorded = useMemo(() => new Map((history.data ?? []).map((row) => [row.student_id, row.status])), [history.data])
  const save = useMutation({
    mutationFn: (records: { student_id: string; attendance_date: string; session: string; status: AttendanceStatus; remarks: null }[]) =>
      postData<AttendanceRecord[], { records: typeof records }>('/attendance/bulk', { records }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['attendance-summary'] })
      await client.invalidateQueries({ queryKey: ['attendance-history'] })
      setToast('Attendance submitted successfully.')
      setStatuses({})
    },
  })
  const studentsToMark = students.data ?? []
  const canMark = canWrite && canRead && canReadStudents
  const pendingStudents = studentsToMark.filter((student) => !recorded.has(student.id))
  const canSubmit = canMark && !history.isLoading && !history.error

  const submit = () => {
    if (!canSubmit || pendingStudents.length === 0) return
    save.mutate(pendingStudents.map((student) => ({
      student_id: student.id,
      attendance_date: attendanceDate,
      session: 'full_day',
      status: statuses[student.id] ?? 'present',
      remarks: null,
    })))
  }

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">Daily operations · Attendance</div><h1>Attendance</h1><p className="subtitle">Select a class and section to load the student register.</p></div>
        {canMark && <button className="button button-primary" disabled={!canSubmit || !pendingStudents.length || save.isPending} onClick={submit} type="button"><Check size={15} />{save.isPending ? 'Submitting…' : history.isLoading ? 'Checking records…' : `Submit attendance${pendingStudents.length ? ` · ${pendingStudents.length}` : ''}`}</button>}
      </div>
      {permissions.error && <div style={{ marginBottom: 15 }}><ErrorState error={permissions.error} onRetry={() => void permissions.refetch()} /></div>}
      {save.error && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(save.error)}</div>}
      <section className="card table-card">
        <div className="attendance-toolbar">
          <div><label className="field-label" htmlFor="attendance-class">Class</label><input autoComplete="off" className="field-input" id="attendance-class" onChange={(event) => { setClassName(event.target.value); setStatuses({}) }} placeholder="e.g. 5" value={className} /></div>
          <div><label className="field-label" htmlFor="attendance-section">Section</label><input autoComplete="off" className="field-input" id="attendance-section" onChange={(event) => { setSection(event.target.value); setStatuses({}) }} placeholder="e.g. A" value={section} /></div>
          <div><label className="field-label" htmlFor="attendance-date">Date</label><input className="field-input" id="attendance-date" onChange={(event) => setAttendanceDate(event.target.value)} type="date" value={attendanceDate} /></div>
        </div>
        {canRead && summary.data && <div className="table-tools" style={{ justifyContent: 'flex-start', gap: 18 }}>
          {(['present', 'absent', 'late', 'excused'] as const).map((status) => <span className="inline-meta" key={status} style={{ gap: 7, fontSize: 11 }}><StatusBadge value={status} /> {summary.data[status] ?? 0}</span>)}
        </div>}
        {!canReadStudents ? <div className="notice" style={{ margin: 14 }}>Your account needs student directory access to load the attendance register.</div> : !className.trim() || !section.trim() ? <div className="empty-state"><div className="empty-icon"><ClipboardCheck size={18} /></div>Enter a class and section above to load its register.</div> : students.isLoading ? <LoadingState label="Loading class register…" /> : students.error ? <ErrorState error={students.error} onRetry={() => void students.refetch()} /> : studentsToMark.length === 0 ? <div className="empty-state"><div className="empty-icon"><CalendarDays size={18} /></div>No active students found for this class and section.</div> : (
          <div>
            {!canMark && <div className="notice" style={{ margin: 14 }}>You can review recorded attendance, but your account needs attendance read/write and student read permissions to submit a register.</div>}
            {canMark && history.error && <div className="notice notice-error" style={{ margin: 14 }}>Existing records could not be checked. Submission is disabled to prevent duplicates.</div>}
            {canMark && studentsToMark.some((student) => recorded.has(student.id)) && <div className="notice" style={{ margin: 14 }}>Existing records for this date are preserved and will be skipped. {pendingStudents.length} students have no attendance record yet.</div>}
            <div className="table-tools"><span className="card-title">{className} · {section}</span><span className="card-subtitle">{studentsToMark.length} active students</span></div>
            <div className="table-wrap"><table><thead><tr><th>Student</th><th>Admission no.</th><th>Roll no.</th><th>Today's record</th>{canWrite && <th>Mark attendance</th>}</tr></thead><tbody>
              {studentsToMark.map((student) => {
                const recordedStatus = recorded.get(student.id)
                return <tr key={student.id}>
                  <td><div className="person-cell"><span className="mini-avatar">{student.first_name[0]}{student.last_name[0]}</span>{student.first_name} {student.last_name}</div></td>
                  <td>{student.admission_number}</td><td>{student.roll_number}</td><td>{recordedStatus ? <StatusBadge value={recordedStatus} /> : <span className="card-subtitle">Not recorded</span>}</td>
                  {canWrite && <td><select aria-label={`Attendance status for ${student.first_name} ${student.last_name}`} className="filter-select" disabled={Boolean(recordedStatus)} onChange={(event) => setStatuses((current) => ({ ...current, [student.id]: event.target.value as AttendanceStatus }))} value={recordedStatus ?? statuses[student.id] ?? 'present'}><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option></select></td>}
                </tr>
              })}
            </tbody></table></div>
          </div>
        )}
      </section>
      {canRead && summary.error && <div style={{ marginTop: 12 }}><ErrorState error={summary.error} onRetry={() => void summary.refetch()} /></div>}
      {history.error && <div style={{ marginTop: 12 }}><ErrorState error={history.error} onRetry={() => void history.refetch()} /></div>}
      {toast && <Toast message={toast} />}
    </>
  )
}

function today() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
