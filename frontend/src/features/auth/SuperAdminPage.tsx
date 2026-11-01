import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, RefreshCw, X } from 'lucide-react'
import { useState } from 'react'
import { api, getApiError, getData } from '../../lib/api'
import type { RegistrationRequest, SuccessEnvelope } from '../../lib/types'

export function SuperAdminPage() {
  const queryClient = useQueryClient()
  const [rejectionReasons, setRejectionReasons] = useState<Record<string, string>>({})
  const [actionError, setActionError] = useState('')
  const [actionNotice, setActionNotice] = useState('')
  const requests = useQuery({
    queryKey: ['registration-requests'],
    queryFn: () => getData<RegistrationRequest[]>('/registration/requests?status=pending'),
    refetchInterval: 30_000,
  })
  const decide = useMutation({
    mutationFn: async ({
      id,
      decision,
      reason,
    }: { id: string; decision: 'approve' | 'reject'; reason?: string }) => {
      const response = await api.post<SuccessEnvelope<RegistrationRequest>>(
        `/registration/requests/${id}/${decision}`,
        decision === 'reject' ? { reason: reason?.trim() || undefined } : {},
      )
      const notification = response.data.meta?.email_notification
      return typeof notification === 'string' ? notification : 'not_reported'
    },
    onSuccess: async (notification) => {
      setActionError('')
      setActionNotice(`Decision saved. Email notification: ${notification}.`)
      setRejectionReasons({})
      await queryClient.invalidateQueries({ queryKey: ['registration-requests'] })
    },
    onError: (error: unknown) => setActionError(getApiError(error)),
  })

  return (
    <section className="page-section">
      <div className="page-heading">
        <div><div className="eyebrow">Access management</div><h1>Registration requests</h1></div>
        <button className="button button-secondary" disabled={requests.isFetching} onClick={() => void requests.refetch()} type="button">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>
      <p className="login-intro">Only the Super Admin can approve or reject new administrator and staff accounts.</p>
      {actionError && <div className="notice notice-error" role="alert">{actionError}</div>}
      {actionNotice && <div className="notice" role="status">{actionNotice}</div>}
      {requests.isPending && <div className="screen-center"><div className="spinner" />Loading requests…</div>}
      {requests.isError && <div className="notice notice-error" role="alert">{getApiError(requests.error)}</div>}
      {requests.data?.length === 0 && <div className="empty-state">There are no pending registration requests.</div>}
      <div className="login-fields">
        {requests.data?.map((request) => (
          <article className="card approval-card" key={request.id}>
            <div className="page-heading">
              <div>
                <h2>{request.full_name}</h2>
                <p>{request.email} · {request.requested_role}</p>
              </div>
              <span className="status-pill">{request.status}</span>
            </div>
            <p>{request.department} · {request.designation}</p>
            {request.employee_id && <p>Employee ID: {request.employee_id}</p>}
            {request.staff_category && <p>Staff category: {request.staff_category}</p>}
            <p>{request.phone_number}</p>
            <p className="footer-note">Verified email · Submitted {new Date(request.created_at).toLocaleString()}</p>
            <div className="login-fields">
              <button
                className="button button-primary"
                disabled={decide.isPending}
                onClick={() => decide.mutate({ id: request.id, decision: 'approve' })}
                type="button"
              >
                <Check size={16} /> Approve
              </button>
              <input
                aria-label={`Rejection reason for ${request.full_name}`}
                className="field-input"
                maxLength={1000}
                onChange={(event) => setRejectionReasons((current) => ({ ...current, [request.id]: event.target.value }))}
                placeholder="Reason (optional)"
                value={rejectionReasons[request.id] ?? ''}
              />
              <button
                className="button button-secondary"
                disabled={decide.isPending}
                onClick={() => decide.mutate({ id: request.id, decision: 'reject', reason: rejectionReasons[request.id] })}
                type="button"
              >
                <X size={16} /> Reject
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
