import { zodResolver } from '@hookform/resolvers/zod'
import { KeyRound, ShieldX } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from './useAuth'
import { supabase } from '../../lib/supabase'

const passwordSchema = z.object({
  currentPassword: z.string().min(1, 'Enter your current password'),
  password: z.string().min(10, 'Use at least 10 characters'),
  confirm: z.string(),
}).refine((value) => value.password === value.confirm, {
  path: ['confirm'],
  message: 'Passwords do not match',
})

export function ChangePasswordPage() {
  const { session } = useAuth()
  const [message, setMessage] = useState('')
  const [failure, setFailure] = useState('')
  const [busy, setBusy] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<{
    currentPassword: string
    password: string
    confirm: string
  }>({ resolver: zodResolver(passwordSchema) })

  const submit = handleSubmit(async ({ currentPassword, password }) => {
    setFailure('')
    setMessage('')
    if (!supabase || !session?.user.email) {
      setFailure('Your authenticated account is unavailable. Sign in again before changing your password.')
      return
    }
    setBusy(true)
    const verified = await supabase.auth.signInWithPassword({
      email: session.user.email,
      password: currentPassword,
    })
    if (verified.error) {
      setBusy(false)
      setFailure('The current password could not be verified.')
      return
    }
    const updated = await supabase.auth.updateUser({ password })
    setBusy(false)
    if (updated.error) setFailure(updated.error.message)
    else setMessage('Your password has been updated.')
  })

  return (
    <section className="card" style={{ maxWidth: 620, margin: '0 auto' }}>
      <div className="card-header"><div><div className="card-title">Change password</div><div className="card-subtitle">Update your Supabase Auth credentials</div></div><KeyRound size={18} color="#8290a4" /></div>
      <div className="card-body">
        <p className="subtitle" style={{ marginTop: 0, marginBottom: 20 }}>Your password is managed securely by Supabase Auth. It is never stored in the school application database.</p>
        {failure && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{failure}</div>}
        {message && <div className="notice" role="status" style={{ marginBottom: 15 }}>{message}</div>}
        <form className="login-fields" onSubmit={(event) => void submit(event)}>
          <div><label className="field-label" htmlFor="current-password">Current password</label><input autoComplete="current-password" className="field-input" id="current-password" type="password" {...register('currentPassword')} />{errors.currentPassword && <div className="field-error">{errors.currentPassword.message}</div>}</div>
          <div><label className="field-label" htmlFor="change-password">New password</label><input autoComplete="new-password" className="field-input" id="change-password" type="password" {...register('password')} />{errors.password && <div className="field-error">{errors.password.message}</div>}</div>
          <div><label className="field-label" htmlFor="confirm-change-password">Confirm new password</label><input autoComplete="new-password" className="field-input" id="confirm-change-password" type="password" {...register('confirm')} />{errors.confirm && <div className="field-error">{errors.confirm.message}</div>}</div>
          <button className="button button-primary" disabled={busy} type="submit">{busy ? 'Updating…' : 'Update password'}</button>
        </form>
      </div>
    </section>
  )
}

export function UnauthorizedPage() {
  return (
    <main className="screen-center" style={{ padding: 20 }}>
      <section className="card" style={{ width: 'min(470px, 100%)', padding: 28 }}>
        <div className="empty-icon" style={{ marginLeft: 0, color: '#b14c4c', background: '#fff0ef' }}><ShieldX size={20} /></div>
        <div className="eyebrow">Access restricted</div>
        <h1 style={{ fontSize: 26 }}>You don’t have access to this page</h1>
        <p className="subtitle" style={{ lineHeight: 1.7 }}>Ask your school administrator if you believe you need this permission.</p>
        <Link className="button button-primary" style={{ marginTop: 18 }} to="/dashboard">Return to workspace</Link>
      </section>
    </main>
  )
}
