import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ClipboardList, Plus, Search, UserRoundCheck, X } from 'lucide-react'
import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { EmptyState, ErrorState, LoadingState, Toast } from '../../components/common/Feedback'
import { Modal } from '../../components/common/Modal'
import { StatusBadge } from '../../components/common/StatusBadge'
import { getApiError, getData, patchData, postData } from '../../lib/api'
import type { Admission, Page, Student } from '../../lib/types'
import { usePermissions } from '../../hooks/usePermissions'

const admissionSchema = z.object({
  application_number: z.string().trim().min(1, 'Application number is required').max(40),
  applicant_name: z.string().trim().min(1, 'Applicant name is required').max(200),
  requested_class: z.string().trim().min(1, 'Class is required').max(32),
  guardian_name: z.string().trim().min(1, 'Guardian name is required').max(200),
  guardian_phone: z.string().trim().min(1, 'Guardian phone is required').max(32),
})
const studentSchema = z.object({
  admission_number: z.string().trim().min(1, 'Admission number is required').max(40),
  first_name: z.string().trim().min(1, 'First name is required').max(100),
  last_name: z.string().trim().min(1, 'Last name is required').max(100),
  date_of_birth: z.string().optional(),
  class_name: z.string().trim().min(1, 'Class is required').max(32),
  section: z.string().trim().min(1, 'Section is required').max(32),
  roll_number: z.string().trim().min(1, 'Roll number is required').max(32),
})
type AdmissionValues = z.infer<typeof admissionSchema>
type StudentValues = z.infer<typeof studentSchema>

export function AdmissionsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [newOpen, setNewOpen] = useState(false)
  const [convert, setConvert] = useState<Admission | null>(null)
  const [toast, setToast] = useState('')
  const client = useQueryClient()
  const permissions = usePermissions()
  const canWrite = permissions.data?.includes('admissions:write') ?? false
  const canApprove = permissions.data?.includes('admissions:approve') ?? false
  const admissions = useQuery({
    queryKey: ['admissions', page],
    queryFn: () => getData<Page<Admission>>('/admissions', { params: { page, page_size: 20 } }),
  })
  const createForm = useForm<AdmissionValues>({
    resolver: zodResolver(admissionSchema),
    defaultValues: { application_number: '', applicant_name: '', requested_class: '', guardian_name: '', guardian_phone: '' },
  })
  const convertForm = useForm<StudentValues>({
    resolver: zodResolver(studentSchema),
  })
  const create = useMutation({
    mutationFn: (values: AdmissionValues) => postData<Admission, AdmissionValues>('/admissions', values),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['admissions'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      setNewOpen(false)
      setToast('Admission application created.')
      createForm.reset()
    },
  })
  const changeStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'under_review' | 'approved' | 'rejected' }) => patchData<Admission, { status: string }>(`/admissions/${id}`, { status }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['admissions'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      setToast('Application status updated.')
    },
  })
  const convertStudent = useMutation({
    mutationFn: ({ admission, values }: { admission: Admission; values: StudentValues }) => postData<Student, Omit<StudentValues, 'date_of_birth'> & { date_of_birth: string | null }>(`/admissions/${admission.id}/convert-to-student`, {
      ...values,
      class_name: admission.requested_class,
      date_of_birth: values.date_of_birth || null,
    }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['admissions'] })
      await client.invalidateQueries({ queryKey: ['students'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      setConvert(null)
      setToast('Approved application converted to a student record.')
      convertForm.reset()
    },
  })
  const rows = useMemo(() => (admissions.data?.items ?? []).filter((row) =>
    `${row.application_number} ${row.applicant_name} ${row.guardian_name} ${row.requested_class}`.toLowerCase().includes(search.toLowerCase()),
  ), [admissions.data, search])

  const openConvert = (application: Admission) => {
    setConvert(application)
    convertForm.reset({
      admission_number: application.application_number,
      first_name: application.applicant_name.split(' ')[0] ?? '',
      last_name: application.applicant_name.split(' ').slice(1).join(' '),
      date_of_birth: '',
      class_name: application.requested_class,
      section: '',
      roll_number: '',
    })
  }

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">Enrolment · Admissions</div><h1>Admissions</h1><p className="subtitle">Review applications and move approved students into the school register.</p></div>
        <div className="heading-actions">{canWrite && <button className="button button-primary" onClick={() => setNewOpen(true)} type="button"><Plus size={16} /> New application</button>}</div>
      </div>
      {(create.error || changeStatus.error || convertStudent.error) && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(create.error ?? changeStatus.error ?? convertStudent.error)}</div>}
      <section className="card table-card">
        <div className="table-tools"><label className="search-box"><Search size={16} /><input aria-label="Search applications" onChange={(event) => setSearch(event.target.value)} placeholder="Search application or applicant…" value={search} /></label><span style={{ color: '#8793a7', fontSize: 11 }}>{admissions.data?.total.toLocaleString() ?? '—'} applications</span></div>
        {admissions.isLoading ? <LoadingState label="Loading applications…" /> : admissions.error ? <ErrorState error={admissions.error} onRetry={() => void admissions.refetch()} /> : rows.length === 0 ? <EmptyState title="No applications found" description={search ? 'Try another search.' : 'Applications will appear here when submitted.'} /> : (
          <div className="table-wrap"><table><thead><tr><th>Application</th><th>Applicant</th><th>Class</th><th>Guardian</th><th>Submitted</th><th>Status</th><th>Actions</th></tr></thead><tbody>
            {rows.map((row) => <tr key={row.id}>
              <td>{row.application_number}</td><td><div className="person-cell"><span className="mini-avatar">{row.applicant_name.slice(0, 1).toUpperCase()}</span>{row.applicant_name}</div></td><td>{row.requested_class}</td><td>{row.guardian_name}<div className="card-subtitle">{row.guardian_phone}</div></td><td>{new Date(row.created_at).toLocaleDateString()}</td><td><StatusBadge value={row.status} /></td>
              <td><div className="row-actions">
                {canApprove && row.status === 'submitted' && <button aria-label={`Review ${row.application_number}`} className="icon-button" onClick={() => changeStatus.mutate({ id: row.id, status: 'under_review' })} title="Move to review" type="button"><ClipboardList size={15} /></button>}
                {canApprove && ['submitted', 'under_review'].includes(row.status) && <><button aria-label={`Approve ${row.application_number}`} className="icon-button" onClick={() => changeStatus.mutate({ id: row.id, status: 'approved' })} title="Approve" type="button"><Check size={15} color="#27835d" /></button><button aria-label={`Reject ${row.application_number}`} className="icon-button" onClick={() => changeStatus.mutate({ id: row.id, status: 'rejected' })} title="Reject" type="button"><X size={15} color="#c14949" /></button></>}
                {canApprove && row.status === 'approved' && <button aria-label={`Convert ${row.application_number} to student`} className="button button-sm" onClick={() => openConvert(row)} type="button"><UserRoundCheck size={14} /> Convert</button>}
              </div></td>
            </tr>)}
          </tbody></table></div>
        )}
        {admissions.data && <div className="pagination">
          <span>Page {admissions.data.page} of {Math.max(admissions.data.total_pages, 1)}</span>
          <div className="pagination-actions">
            <button className="button button-sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button">Previous</button>
            <button className="button button-sm" disabled={page >= admissions.data.total_pages} onClick={() => setPage((value) => value + 1)} type="button">Next</button>
          </div>
        </div>}
      </section>
      {newOpen && <Modal title="New admission application" description="Record an applicant and guardian contact." onClose={() => setNewOpen(false)} footer={<><button className="button" onClick={() => setNewOpen(false)} type="button">Cancel</button><button className="button button-primary" disabled={create.isPending} form="admission-form" type="submit">{create.isPending ? 'Saving…' : 'Create application'}</button></>}>
        <form className="form-grid" id="admission-form" onSubmit={(event) => void createForm.handleSubmit((values) => create.mutate(values))(event)}>
          <Field id="application-number" label="Application number" error={createForm.formState.errors.application_number?.message}><input className="field-input" id="application-number" {...createForm.register('application_number')} /></Field>
          <Field id="applicant-name" label="Applicant name" error={createForm.formState.errors.applicant_name?.message}><input className="field-input" id="applicant-name" {...createForm.register('applicant_name')} /></Field>
          <Field id="requested-class" label="Requested class" error={createForm.formState.errors.requested_class?.message}><input className="field-input" id="requested-class" {...createForm.register('requested_class')} /></Field>
          <Field id="guardian-name" label="Guardian name" error={createForm.formState.errors.guardian_name?.message}><input className="field-input" id="guardian-name" {...createForm.register('guardian_name')} /></Field>
          <Field id="guardian-phone" label="Guardian phone" error={createForm.formState.errors.guardian_phone?.message}><input className="field-input" id="guardian-phone" {...createForm.register('guardian_phone')} /></Field>
        </form>
      </Modal>}
      {convert && <Modal title="Convert to student" description={`Create the student record for ${convert.applicant_name}. Class is fixed to the approved class ${convert.requested_class}.`} onClose={() => setConvert(null)} footer={<><button className="button" onClick={() => setConvert(null)} type="button">Cancel</button><button className="button button-primary" disabled={convertStudent.isPending} form="convert-form" type="submit">{convertStudent.isPending ? 'Converting…' : 'Create student record'}</button></>}>
        {convertStudent.error && <div className="notice notice-error" role="alert" style={{ marginBottom: 14 }}>{getApiError(convertStudent.error)}</div>}
        <form className="form-grid" id="convert-form" onSubmit={(event) => void convertForm.handleSubmit((values) => convertStudent.mutate({ admission: convert, values }))(event)}>
          <Field id="convert-admission" label="Admission number" error={convertForm.formState.errors.admission_number?.message}><input className="field-input" id="convert-admission" {...convertForm.register('admission_number')} /></Field>
          <Field id="convert-first" label="First name" error={convertForm.formState.errors.first_name?.message}><input className="field-input" id="convert-first" {...convertForm.register('first_name')} /></Field>
          <Field id="convert-last" label="Last name" error={convertForm.formState.errors.last_name?.message}><input className="field-input" id="convert-last" {...convertForm.register('last_name')} /></Field>
          <Field id="convert-dob" label="Date of birth"><input className="field-input" id="convert-dob" type="date" {...convertForm.register('date_of_birth')} /></Field>
          <Field id="convert-class" label="Class"><input className="field-input" disabled id="convert-class" {...convertForm.register('class_name')} /></Field>
          <Field id="convert-section" label="Section" error={convertForm.formState.errors.section?.message}><input className="field-input" id="convert-section" {...convertForm.register('section')} /></Field>
          <Field id="convert-roll" label="Roll number" error={convertForm.formState.errors.roll_number?.message}><input className="field-input" id="convert-roll" {...convertForm.register('roll_number')} /></Field>
        </form>
      </Modal>}
      {toast && <Toast message={toast} />}
    </>
  )
}

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return <div className="form-field"><label className="field-label" htmlFor={id}>{label}</label>{children}{error && <div className="field-error">{error}</div>}</div>
}
