import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, KeyRound } from 'lucide-react'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { supabase } from '../../lib/supabase'

const emailSchema = z.object({ email: z.string().email('Enter a valid email address') })
const passwordSchema = z.object({
  password: z.string().min(10, 'Use at least 10 characters'),
  confirm: z.string(),
}).refine((value) => value.password === value.confirm, {
  path: ['confirm'],
  message: 'Passwords do not match',
})

export function ForgotPasswordPage() {
  const [message, setMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<{ email: string }>({
    resolver: zodResolver(emailSchema),
  })

  const submit = handleSubmit(async ({ email }) => {
    setErrorMessage('')
    setMessage('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add frontend/.env settings to enable password reset.')
      return
    }
    setBusy(true)
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    setBusy(false)
    if (error) setErrorMessage(error.message)
    else setMessage('If an account exists for this address, a password reset link is on its way.')
  })

  return (
    <AuthPage title="Reset your password" description="Enter your school email and Supabase will send a secure reset link.">
      {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}</div>}
      {message && <div className="notice" role="status">{message}</div>}
      <form className="login-fields" onSubmit={(event) => void submit(event)}>
        <div>
          <label className="field-label" htmlFor="reset-email">Email address</label>
          <input className="field-input" id="reset-email" type="email" {...register('email')} />
          {errors.email && <div className="field-error">{errors.email.message}</div>}
        </div>
        <button className="button button-primary login-submit" disabled={busy} type="submit">{busy ? 'Sending…' : 'Send reset link'}</button>
      </form>
    </AuthPage>
  )
}

export function ResetPasswordPage() {
  const [message, setMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<{ password: string; confirm: string }>({
    resolver: zodResolver(passwordSchema),
  })

  const submit = handleSubmit(async ({ password }) => {
    setErrorMessage('')
    setMessage('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Contact your school administrator.')
      return
    }
    setBusy(true)
    const { error } = await supabase.auth.updateUser({ password })
    setBusy(false)
    if (error) setErrorMessage(error.message)
    else setMessage('Password updated. You can now sign in with your new password.')
  })

  return (
    <AuthPage title="Choose a new password" description="Set a new password for your school account.">
      {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}</div>}
      {message && <div className="notice" role="status">{message}</div>}
      <form className="login-fields" onSubmit={(event) => void submit(event)}>
        <div>
          <label className="field-label" htmlFor="new-password">New password</label>
          <input className="field-input" id="new-password" type="password" autoComplete="new-password" {...register('password')} />
          {errors.password && <div className="field-error">{errors.password.message}</div>}
        </div>
        <div>
          <label className="field-label" htmlFor="confirm-password">Confirm password</label>
          <input className="field-input" id="confirm-password" type="password" autoComplete="new-password" {...register('confirm')} />
          {errors.confirm && <div className="field-error">{errors.confirm.message}</div>}
        </div>
        <button className="button button-primary login-submit" disabled={busy} type="submit">{busy ? 'Updating…' : 'Update password'}</button>
      </form>
    </AuthPage>
  )
}

function AuthPage({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <main className="screen-center" style={{ padding: 20 }}>
      <section className="card" style={{ width: 'min(420px, 100%)', padding: 28 }}>
        <div className="empty-icon" style={{ marginLeft: 0 }}><KeyRound size={19} /></div>
        <h1 style={{ fontSize: 24 }}>{title}</h1>
        <p className="subtitle" style={{ marginBottom: 22 }}>{description}</p>
        {children}
        <Link className="text-link" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, marginTop: 22, fontSize: 12 }} to="/login">
          <ArrowLeft size={14} /> Back to sign in
        </Link>
      </section>
    </main>
  )
}
