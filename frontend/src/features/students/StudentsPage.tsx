import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, Eye, Plus, Search } from 'lucide-react'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { EmptyState, ErrorState, LoadingState } from '../../components/common/Feedback'
import { Modal } from '../../components/common/Modal'
import { StatusBadge } from '../../components/common/StatusBadge'
import { getApiError, getData, postData } from '../../lib/api'
import type { Page, Student } from '../../lib/types'

const studentSchema = z.object({
  admission_number: z.string().trim().min(1, 'Admission number is required').max(40),
  first_name: z.string().trim().min(1, 'First name is required').max(100),
  last_name: z.string().trim().min(1, 'Last name is required').max(100),
  date_of_birth: z.string().optional(),
  class_name: z.string().trim().min(1, 'Class is required').max(32),
  section: z.string().trim().min(1, 'Section is required').max(32),
  roll_number: z.string().trim().min(1, 'Roll number is required').max(32),
})
type StudentValues = z.infer<typeof studentSchema>

export function StudentsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [toast, setToast] = useState('')
  const client = useQueryClient()
  const students = useQuery({
    queryKey: ['students', 'list', page, search],
    queryFn: () => getData<Page<Student>>('/students', { params: { page, page_size: 20, ...(search ? { search } : {}) } }),
  })
  const createStudent = useMutation({
    mutationFn: (values: StudentValues) => postData<Student, Omit<StudentValues, 'date_of_birth'> & { date_of_birth: string | null }>('/students', {
      ...values,
      date_of_birth: values.date_of_birth || null,
    }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['students'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      setDialogOpen(false)
      setToast('Student record created.')
      form.reset()
    },
  })
  const form = useForm<StudentValues>({
    resolver: zodResolver(studentSchema),
    defaultValues: { admission_number: '', first_name: '', last_name: '', date_of_birth: '', class_name: '', section: '', roll_number: '' },
  })
  const rows = students.data?.items ?? []
  const error = createStudent.error

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">People · Students</div><h1>Students</h1><p className="subtitle">School student records and enrolment details.</p></div>
        <div className="heading-actions"><button className="button button-primary" onClick={() => setDialogOpen(true)} type="button"><Plus size={16} /> Add student</button></div>
      </div>
      {error && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(error)}</div>}
      <section className="card table-card">
        <div className="table-tools">
          <label className="search-box"><Search size={16} /><input aria-label="Search students" onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search name or admission number…" value={search} /></label>
          <div className="inline-meta" style={{ color: '#8793a7', fontSize: 11 }}>{students.data?.total.toLocaleString() ?? '—'} records</div>
        </div>
        {students.isLoading ? <LoadingState label="Loading student records…" /> : students.error ? <ErrorState error={students.error} onRetry={() => void students.refetch()} /> : rows.length === 0 ? <EmptyState title="No student records found" description={search ? 'Try another search phrase.' : 'Add a student to begin building the directory.'} /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Student</th><th>Admission no.</th><th>Class</th><th>Roll no.</th><th>Status</th><th><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {rows.map((student) => <StudentRow key={student.id} student={student} />)}
              </tbody>
            </table>
          </div>
        )}
        {students.data && <div className="pagination">
          <span>Page {students.data.page} of {Math.max(students.data.total_pages, 1)}</span>
          <div className="pagination-actions">
            <button className="button button-sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button"><ArrowUp size={13} /> Previous</button>
            <button className="button button-sm" disabled={page >= students.data.total_pages} onClick={() => setPage((value) => value + 1)} type="button"><ArrowDown size={13} /> Next</button>
          </div>
        </div>}
      </section>
      {dialogOpen && <Modal
        title="Add a student"
        description="Create a student record in this school's directory."
        onClose={() => { setDialogOpen(false); createStudent.reset() }}
        footer={<><button className="button" onClick={() => setDialogOpen(false)} type="button">Cancel</button><button className="button button-primary" disabled={createStudent.isPending} form="student-create-form" type="submit">{createStudent.isPending ? 'Saving…' : 'Create student'}</button></>}
      >
        <form className="form-grid" id="student-create-form" onSubmit={(event) => void form.handleSubmit((values) => createStudent.mutate(values))(event)}>
          <Field label="Admission number" error={form.formState.errors.admission_number?.message}><input className="field-input" {...form.register('admission_number')} /></Field>
          <Field label="Date of birth" error={form.formState.errors.date_of_birth?.message}><input className="field-input" type="date" {...form.register('date_of_birth')} /></Field>
          <Field label="First name" error={form.formState.errors.first_name?.message}><input className="field-input" {...form.register('first_name')} /></Field>
          <Field label="Last name" error={form.formState.errors.last_name?.message}><input className="field-input" {...form.register('last_name')} /></Field>
          <Field label="Class" error={form.formState.errors.class_name?.message}><input className="field-input" {...form.register('class_name')} /></Field>
          <Field label="Section" error={form.formState.errors.section?.message}><input className="field-input" {...form.register('section')} /></Field>
          <Field label="Roll number" error={form.formState.errors.roll_number?.message}><input className="field-input" {...form.register('roll_number')} /></Field>
        </form>
      </Modal>}
      {toast && <button className="toast" onClick={() => setToast('')} type="button">{toast}</button>}
    </>
  )
}

function StudentRow({ student }: { student: Student }) {
  const fullName = `${student.first_name} ${student.last_name}`
  return (
    <tr>
      <td><div className="person-cell"><span className="mini-avatar">{fullName.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}</span><Link className="table-link" to={`/students/${student.id}`}>{fullName}</Link></div></td>
      <td>{student.admission_number}</td>
      <td>{student.class_name} · {student.section}</td>
      <td>{student.roll_number}</td>
      <td><StatusBadge value={student.status} /></td>
      <td><Link aria-label={`View ${fullName}`} className="icon-button" to={`/students/${student.id}`}><Eye size={16} /></Link></td>
    </tr>
  )
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return <div className="form-field"><label className="field-label">{label}{children}</label>{error && <div className="field-error">{error}</div>}</div>
}
