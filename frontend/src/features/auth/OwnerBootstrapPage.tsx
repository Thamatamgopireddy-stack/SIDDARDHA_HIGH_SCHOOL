import { ArrowRight } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { getApiError, postData } from '../../lib/api'
import { supabase } from '../../lib/supabase'
import { useAuth } from './useAuth'

export function OwnerBootstrapPage() {
  const navigate = useNavigate()
  const { session, refreshAccountStatus, signOut } = useAuth()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const sendCode = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add the public URL and anon key to frontend/.env.')
      return
    }
    setSubmitting(true)
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim().toLowerCase(),
        options: { shouldCreateUser: true },
      })
      if (error) {
        setErrorMessage(getSupabaseError(error))
        return
      }
      setCodeSent(true)
    } catch (error) {
      setErrorMessage(getSupabaseError(error))
    } finally {
      setSubmitting(false)
    }
  }

  const verifyCode = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    if (!supabase) return
    if (!/^\d{6}$/.test(code.trim())) {
      setErrorMessage('Enter the six-digit code from your email.')
      return
    }
    setSubmitting(true)
    try {
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim().toLowerCase(),
        token: code.trim(),
        type: 'email',
      })
      if (error) setErrorMessage(getSupabaseError(error))
    } catch (error) {
      setErrorMessage(getSupabaseError(error))
    } finally {
      setSubmitting(false)
    }
  }

  const bootstrap = async () => {
    setErrorMessage('')
    setSubmitting(true)
    try {
      await postData('/auth/bootstrap-super-admin', {})
      await refreshAccountStatus()
      navigate('/account-status', { replace: true })
    } catch (error) {
      setErrorMessage(getApiError(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="screen-center" style={{ padding: 24 }}>
      <section className="login-form" style={{ maxWidth: 520, width: '100%' }}>
        <div className="eyebrow">One-time owner setup</div>
        <h2>{session ? 'Initialize Super Admin access' : codeSent ? 'Verify the owner email' : 'Verify the configured owner email'}</h2>
        <p className="login-intro">
          The backend allows only its configured, verified owner email to claim Super Admin access, and only once.
        </p>
        {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}</div>}
        {!session && (
          <form className="login-fields" onSubmit={(event) => {
            if (codeSent) void verifyCode(event)
            else void sendCode(event)
          }}>
            {!codeSent ? (
              <>
                <label className="field-label" htmlFor="owner-email">Owner email</label>
                <input autoComplete="email" className="field-input" id="owner-email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Sending code…' : 'Send owner verification code'} {!submitting && <ArrowRight size={16} />}
                </button>
              </>
            ) : (
              <>
                <label className="field-label" htmlFor="owner-code">Six-digit email code</label>
                <input
                  autoComplete="one-time-code"
                  className="field-input"
                  id="owner-code"
                  inputMode="numeric"
                  maxLength={6}
                  onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
                  value={code}
                />
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Verifying…' : 'Verify owner email'} {!submitting && <ArrowRight size={16} />}
                </button>
              </>
            )}
          </form>
        )}
        {session && (
          <div className="login-fields">
            <button className="button button-primary login-submit" disabled={submitting} onClick={() => void bootstrap()} type="button">
              {submitting ? 'Verifying owner…' : 'Claim Super Admin account'}
            </button>
            <button className="text-link" onClick={() => void signOut()} type="button">Sign out and use a different email</button>
          </div>
        )}
      </section>
    </main>
  )
}

function getSupabaseError(error: unknown): string {
  const message = error instanceof Error ? error.message : ''
  if (/failed to fetch|network|fetch failed/i.test(message)) {
    return 'Could not reach Supabase Auth. Check that VITE_SUPABASE_URL in frontend/.env exactly matches the Project URL shown in your Supabase dashboard, and that the project is active. Then restart the frontend.'
  }
  return message || 'Supabase Auth could not complete the request. Please try again.'
}
