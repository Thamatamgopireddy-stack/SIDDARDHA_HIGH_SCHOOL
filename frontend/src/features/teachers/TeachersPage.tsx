import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, UsersRound } from 'lucide-react'
import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { EmptyState, ErrorState, LoadingState, Toast } from '../../components/common/Feedback'
import { Modal } from '../../components/common/Modal'
import { StatusBadge } from '../../components/common/StatusBadge'
import { getApiError, getData, postData } from '../../lib/api'
import type { Page, Teacher } from '../../lib/types'

const schema = z.object({
  employee_number: z.string().trim().min(1, 'Employee number is required').max(40),
  first_name: z.string().trim().min(1, 'First name is required').max(100),
  last_name: z.string().trim().min(1, 'Last name is required').max(100),
  email: z.union([z.string().email('Enter a valid email address'), z.literal('')]).optional(),
  phone: z.string().max(32).optional(),
})
type Values = z.infer<typeof schema>
type CreateBody = Omit<Values, 'email' | 'phone'> & { email: string | null; phone: string | null }

export function TeachersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState('')
  const client = useQueryClient()
  const teachers = useQuery({
    queryKey: ['teachers', page],
    queryFn: () => getData<Page<Teacher>>('/teachers', { params: { page, page_size: 20 } }),
  })
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { employee_number: '', first_name: '', last_name: '', email: '', phone: '' } })
  const create = useMutation({
    mutationFn: (values: Values) => postData<Teacher, CreateBody>('/teachers', {
      ...values, email: values.email || null, phone: values.phone || null,
    }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['teachers'] })
      await client.invalidateQueries({ queryKey: ['dashboard'] })
      setOpen(false)
      setToast('Teacher record created.')
      form.reset()
    },
  })
  const rows = useMemo(() => (teachers.data?.items ?? []).filter((row) => {
    const text = `${row.first_name} ${row.last_name} ${row.employee_number} ${row.email ?? ''}`.toLowerCase()
    return text.includes(search.toLowerCase())
  }), [teachers.data, search])

  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">People · Employees</div><h1>Teachers</h1><p className="subtitle">Teacher directory for {import.meta.env.VITE_APP_SCHOOL_NAME || 'SIDDARDHA HIGH SCHOOL'}.</p></div>
        <div className="heading-actions"><button className="button button-primary" onClick={() => setOpen(true)} type="button"><Plus size={16} /> Add teacher</button></div>
      </div>
      {create.error && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(create.error)}</div>}
      <section className="card table-card">
        <div className="table-tools"><label className="search-box"><Search size={16} /><input aria-label="Search teachers on this page" onChange={(event) => setSearch(event.target.value)} placeholder="Search current page…" value={search} /></label><span style={{ color: '#8793a7', fontSize: 11 }}>{teachers.data?.total.toLocaleString() ?? '—'} records</span></div>
        {teachers.isLoading ? <LoadingState label="Loading teachers…" /> : teachers.error ? <ErrorState error={teachers.error} onRetry={() => void teachers.refetch()} /> : rows.length === 0 ? <EmptyState title="No teacher records found" description={search ? 'Try another search.' : 'Add a teacher to create the directory.'} /> : (
          <div className="table-wrap"><table><thead><tr><th>Teacher</th><th>Employee no.</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead><tbody>
            {rows.map((teacher) => <tr key={teacher.id}><td><div className="person-cell"><span className="mini-avatar">{teacher.first_name[0]}{teacher.last_name[0]}</span>{teacher.first_name} {teacher.last_name}</div></td><td>{teacher.employee_number}</td><td>{teacher.email ?? '—'}</td><td>{teacher.phone ?? '—'}</td><td><StatusBadge value={teacher.status} /></td></tr>)}
          </tbody></table></div>
        )}
        {teachers.data && <div className="pagination"><span>Page {page} of {Math.max(teachers.data.total_pages, 1)}</span><div className="pagination-actions"><button className="button button-sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button">Previous</button><button className="button button-sm" disabled={page >= teachers.data.total_pages} onClick={() => setPage((value) => value + 1)} type="button">Next</button></div></div>}
      </section>
      {!teachers.isLoading && !teachers.error && rows.length === 0 && !search && <div className="footer-note"><UsersRound size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} />This directory currently supports read and create operations in the connected API.</div>}
      {open && <Modal title="Add a teacher" description="Create an employee record in the school directory." onClose={() => setOpen(false)} footer={<><button className="button" onClick={() => setOpen(false)} type="button">Cancel</button><button className="button button-primary" disabled={create.isPending} form="teacher-form" type="submit">{create.isPending ? 'Saving…' : 'Create teacher'}</button></>}>
        <form className="form-grid" id="teacher-form" onSubmit={(event) => void form.handleSubmit((values) => create.mutate(values))(event)}>
          <Field label="Employee number" id="employee-number" error={form.formState.errors.employee_number?.message}><input className="field-input" id="employee-number" {...form.register('employee_number')} /></Field>
          <Field label="First name" id="teacher-first" error={form.formState.errors.first_name?.message}><input className="field-input" id="teacher-first" {...form.register('first_name')} /></Field>
          <Field label="Last name" id="teacher-last" error={form.formState.errors.last_name?.message}><input className="field-input" id="teacher-last" {...form.register('last_name')} /></Field>
          <Field label="Email" id="teacher-email" error={form.formState.errors.email?.message}><input className="field-input" id="teacher-email" type="email" {...form.register('email')} /></Field>
          <Field label="Phone" id="teacher-phone"><input className="field-input" id="teacher-phone" {...form.register('phone')} /></Field>
        </form>
      </Modal>}
      {toast && <Toast message={toast} />}
    </>
  )
}

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return <div className="form-field"><label className="field-label" htmlFor={id}>{label}</label>{children}{error && <div className="field-error">{error}</div>}</div>
}
