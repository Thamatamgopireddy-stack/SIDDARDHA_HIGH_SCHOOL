import { ArrowRight, RefreshCw, ShieldCheck } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'

const descriptions: Record<string, { title: string; message: string }> = {
  pending: {
    title: 'Request under review',
    message: 'Your email is verified. The school Super Admin will review your account request before ERP access is enabled.',
  },
  rejected: {
    title: 'Request not approved',
    message: 'Your registration request was not approved. Review the note below or contact the school administrator.',
  },
  suspended: {
    title: 'Account suspended',
    message: 'ERP access is temporarily suspended. Contact the school Super Admin for assistance.',
  },
  disabled: {
    title: 'Account disabled',
    message: 'This account does not currently have ERP access. Contact the school Super Admin for assistance.',
  },
  not_registered: {
    title: 'Finish setting up your account',
    message: 'Your email is verified, but no school registration request is linked to this account yet.',
  },
}

export function AccountStatusPage() {
  const location = useLocation()
  const { accountStatus, statusError, loading, refreshAccountStatus, signOut } = useAuth()
  const routeState = location.state as {
    emailNotification?: string
    statusRefreshError?: string | null
  } | null
  const emailNotification = routeState?.emailNotification
  const state = accountStatus?.account_status ?? ''
  const content = descriptions[state] ?? {
    title: state === 'approved' ? 'No access role assigned' : 'Account needs attention',
    message: state === 'approved'
      ? 'Your account is approved, but no portal role is assigned. Contact the school Super Admin.'
      : 'Your account is not ready for ERP access. Contact the school Super Admin.',
  }

  if (loading && !accountStatus) {
    return <main className="screen-center" aria-live="polite"><div className="spinner" />Checking account status…</main>
  }

  return (
    <main className="screen-center" style={{ padding: 24 }}>
      <section className="login-form" style={{ maxWidth: 520, width: '100%' }}>
        <div className="brand-mark"><ShieldCheck size={22} /></div>
        <div className="eyebrow">EduCore account</div>
        <h2>{statusError ? 'Could not verify account status' : content.title}</h2>
        <p className="login-intro">{statusError || content.message}</p>
        {emailNotification && (
          <div className="notice" role="status">
            Your registration request was submitted. Email notification: {emailNotification}.
          </div>
        )}
        {routeState?.statusRefreshError && (
          <div className="notice notice-error" role="alert">
            The registration request was saved, but status refresh failed: {routeState.statusRefreshError}
          </div>
        )}
        {accountStatus?.email && <p className="footer-note">{accountStatus.email}</p>}
        {accountStatus?.rejection_reason && (
          <div className="notice notice-error"><strong>Review note:</strong> {accountStatus.rejection_reason}</div>
        )}
        {accountStatus?.email_verified === false && (
          <div className="notice notice-error">Verify your email address before continuing.</div>
        )}
        {state === 'not_registered' && (
          <div className="login-fields">
            <Link className="button button-primary login-submit" to="/register/admin">Request administrator access <ArrowRight size={16} /></Link>
            <Link className="button button-secondary login-submit" to="/register/staff">Request staff access</Link>
            <Link className="text-link" to="/owner-bootstrap">First-time Super Admin setup</Link>
          </div>
        )}
        {state === 'rejected' && (
          <div className="login-fields">
            <Link className="button button-secondary login-submit" to={`/register/${accountStatus?.requested_role ?? 'staff'}`}>Submit a new request</Link>
          </div>
        )}
        <div className="login-fields">
          <button
            className="button button-secondary"
            disabled={loading}
            onClick={() => void refreshAccountStatus().catch(() => undefined)}
            type="button"
          >
            <RefreshCw size={16} /> Refresh status
          </button>
          <button className="text-link" onClick={() => void signOut()} type="button">Sign out</button>
        </div>
      </section>
    </main>
  )
}
