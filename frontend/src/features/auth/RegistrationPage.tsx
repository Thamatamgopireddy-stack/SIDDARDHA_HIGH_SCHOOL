import { ArrowLeft, ArrowRight, GraduationCap } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, getApiError } from '../../lib/api'
import { appConfig } from '../../lib/env'
import { supabase } from '../../lib/supabase'
import type { RegistrationRequest, SuccessEnvelope } from '../../lib/types'
import { useAuth } from './useAuth'

type RegistrationRole = 'admin' | 'staff'

interface RegistrationValues {
  full_name: string
  email: string
  phone_number: string
  employee_id: string
  department: string
  designation: string
  staff_category: string
}

const emptyValues: RegistrationValues = {
  full_name: '',
  email: '',
  phone_number: '',
  employee_id: '',
  department: '',
  designation: '',
  staff_category: '',
}

export function RegistrationPage() {
  const { role: roleParam } = useParams()
  const role: RegistrationRole = roleParam === 'staff' ? 'staff' : 'admin'
  const navigate = useNavigate()
  const { refreshAccountStatus } = useAuth()
  const [values, setValues] = useState(emptyValues)
  const [code, setCode] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [notice, setNotice] = useState('')

  const update = (key: keyof RegistrationValues, value: string) => {
    setValues((current) => ({ ...current, [key]: value }))
  }

  const sendCode = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    setNotice('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add the public URL and anon key to frontend/.env.')
      return
    }
    if (!values.full_name.trim() || !values.email.trim() || !values.department.trim() || !values.designation.trim()) {
      setErrorMessage('Complete all required fields before requesting a verification code.')
      return
    }
    if (role === 'staff' && (!values.employee_id.trim() || !values.staff_category.trim())) {
      setErrorMessage('Staff ID and staff category are required for staff registration.')
      return
    }
    setSubmitting(true)
    const { error } = await supabase.auth.signInWithOtp({
      email: values.email.trim().toLowerCase(),
      options: {
        shouldCreateUser: true,
        data: { full_name: values.full_name.trim() },
      },
    })
    setSubmitting(false)
    if (error) {
      setErrorMessage(error.message)
      return
    }
    setCodeSent(true)
    setNotice('A verification code has been sent to your email.')
  }

  const verifyAndSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    setNotice('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add the public URL and anon key to frontend/.env.')
      return
    }
    if (!/^\d{6}$/.test(code.trim())) {
      setErrorMessage('Enter the six-digit code from your email.')
      return
    }
    setSubmitting(true)
    const { error: verifyError } = await supabase.auth.verifyOtp({
      email: values.email.trim().toLowerCase(),
      token: code.trim(),
      type: 'email',
    })
    if (verifyError) {
      setSubmitting(false)
      setErrorMessage(verifyError.message)
      return
    }
    const payload = {
      full_name: values.full_name.trim(),
      email: values.email.trim().toLowerCase(),
      phone_number: values.phone_number.trim(),
      employee_id: values.employee_id.trim() || null,
      department: values.department.trim(),
      designation: values.designation.trim(),
      ...(role === 'staff' ? { staff_category: values.staff_category.trim() } : {}),
    }
    try {
      const response = await api.post<SuccessEnvelope<RegistrationRequest>>(
        `/registration/${role}`,
        payload,
      )
      let statusRefreshError: string | null = null
      try {
        await refreshAccountStatus()
      } catch (refreshError) {
        statusRefreshError = getApiError(refreshError)
      }
      const notification = response.data.meta?.email_notification
      navigate('/account-status', {
        replace: true,
        state: {
          emailNotification: typeof notification === 'string' ? notification : 'not_reported',
          statusRefreshError,
        },
      })
    } catch (error) {
      setErrorMessage(getApiError(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-layout">
      <section className="login-brand-panel">
        <div className="brand">
          <div className="brand-mark"><GraduationCap size={22} /></div>
          <div><div className="brand-name">{appConfig.appName}</div><div className="brand-subtitle" style={{ color: '#d8e0ff' }}>{appConfig.schoolName}</div></div>
        </div>
        <div className="login-hero">
          <div className="eyebrow" style={{ color: '#cbd6ff' }}>Secure registration</div>
          <h1>{role === 'admin' ? 'Administrator access' : 'Staff access'}</h1>
          <p>Verify your school email, then submit your details for Super Admin review.</p>
        </div>
        <div className="login-copy">© {new Date().getFullYear()} {appConfig.schoolName}</div>
      </section>
      <section className="login-form-panel">
        <form className="login-form" onSubmit={(event) => {
          if (codeSent) void verifyAndSubmit(event)
          else void sendCode(event)
        }}>
          <div className="eyebrow">{codeSent ? 'Email verification' : 'Account request'}</div>
          <h2>{codeSent ? 'Verify your email' : `Request ${role} access`}</h2>
          <p className="login-intro">
            {codeSent
              ? `Enter the code sent to ${values.email}.`
              : 'All fields are reviewed by the school before ERP access is granted.'}
          </p>
          {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}</div>}
          {notice && <div className="notice" role="status">{notice}</div>}
          <div className="login-fields">
            {!codeSent ? (
              <>
                <Field label="Full name" value={values.full_name} onChange={(value) => update('full_name', value)} required />
                <Field label="Email address" type="email" value={values.email} onChange={(value) => update('email', value)} required />
                <Field label="Phone number" type="tel" value={values.phone_number} onChange={(value) => update('phone_number', value)} required />
                {role === 'staff' && <Field label="Staff / employee ID" value={values.employee_id} onChange={(value) => update('employee_id', value)} required />}
                <Field label="Department" value={values.department} onChange={(value) => update('department', value)} required />
                <Field label="Designation" value={values.designation} onChange={(value) => update('designation', value)} required />
                {role === 'staff' && <Field label="Staff category" value={values.staff_category} onChange={(value) => update('staff_category', value)} required />}
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Sending code…' : 'Verify email'} {!submitting && <ArrowRight size={16} />}
                </button>
              </>
            ) : (
              <>
                <label className="field-label" htmlFor="registration-code">Six-digit email code</label>
                <input
                  autoComplete="one-time-code"
                  className="field-input"
                  id="registration-code"
                  inputMode="numeric"
                  maxLength={6}
                  onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  value={code}
                />
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Submitting…' : 'Verify and submit request'} {!submitting && <ArrowRight size={16} />}
                </button>
                <button className="text-link" onClick={() => setCodeSent(false)} type="button">Edit registration details</button>
              </>
            )}
          </div>
          <div className="footer-note">
            <Link className="text-link" to="/"><ArrowLeft size={14} /> Back</Link>
            {' · '}
            <Link className="text-link" to="/login">Already registered? Sign in</Link>
          </div>
        </form>
      </section>
    </main>
  )
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  required?: boolean
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, '-')
  return (
    <div>
      <label className="field-label" htmlFor={id}>{label}</label>
      <input
        autoComplete={type === 'email' ? 'email' : undefined}
        className="field-input"
        id={id}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        type={type}
        value={value}
      />
    </div>
  )
}
