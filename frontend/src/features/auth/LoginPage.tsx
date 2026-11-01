import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowRight, GraduationCap, ShieldCheck } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { supabase } from '../../lib/supabase'
import { appConfig } from '../../lib/env'

const emailSchema = z.object({
  email: z.string().email('Enter a valid email address'),
})
type LoginValues = z.infer<typeof emailSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const [errorMessage, setErrorMessage] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const [code, setCode] = useState('')
  const [cooldown, setCooldown] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const timer = useRef<number | null>(null)
  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(emailSchema) })

  useEffect(() => () => {
    if (timer.current !== null) window.clearInterval(timer.current)
  }, [])

  const startCooldown = () => {
    setCooldown(60)
    if (timer.current !== null) window.clearInterval(timer.current)
    timer.current = window.setInterval(() => {
      setCooldown((value) => {
        if (value <= 1) {
          if (timer.current !== null) window.clearInterval(timer.current)
          timer.current = null
          return 0
        }
        return value - 1
      })
    }, 1000)
  }

  const sendCode = async (email: string) => {
    setErrorMessage('')
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add the public URL and anon key to frontend/.env.')
      return
    }
    setSubmitting(true)
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: false },
    })
    setSubmitting(false)
    if (error) {
      setErrorMessage(error.message)
      return
    }
    setCodeSent(true)
    startCooldown()
  }

  const submitEmail = handleSubmit(async ({ email }) => sendCode(email.trim().toLowerCase()))

  const verifyCode = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    const email = getValues('email').trim().toLowerCase()
    if (!supabase) {
      setErrorMessage('Supabase is not configured. Add the public URL and anon key to frontend/.env.')
      return
    }
    if (!/^\d{6}$/.test(code.trim())) {
      setErrorMessage('Enter the six-digit code from your email.')
      return
    }
    setSubmitting(true)
    const { error } = await supabase.auth.verifyOtp({
      email,
      token: code.trim(),
      type: 'email',
    })
    setSubmitting(false)
    if (error) {
      setErrorMessage(error.message)
      return
    }
    navigate('/account-status', { replace: true })
  }

  return (
    <main className="login-layout">
      <section className="login-brand-panel">
        <div className="brand">
          <div className="brand-mark"><GraduationCap size={22} /></div>
          <div>
            <div className="brand-name">{appConfig.appName}</div>
            <div className="brand-subtitle" style={{ color: '#d8e0ff' }}>{appConfig.schoolName}</div>
          </div>
        </div>
        <div className="login-hero">
          <div className="eyebrow" style={{ color: '#cbd6ff' }}>A connected school community</div>
          <h1>Everything school, in one place.</h1>
          <p>One secure workspace for the people and everyday work that move our school forward.</p>
          <div className="login-feature"><ShieldCheck size={17} /> Secure access with a one-time email code</div>
        </div>
        <div className="login-copy">© {new Date().getFullYear()} {appConfig.schoolName}</div>
      </section>
      <section className="login-form-panel">
        <form className="login-form" onSubmit={(event) => {
          if (codeSent) void verifyCode(event)
          else void submitEmail(event)
        }}>
          <div className="eyebrow">Welcome back</div>
          <h2>{codeSent ? 'Check your email' : 'Sign in securely'}</h2>
          <p className="login-intro">
            {codeSent
              ? `Enter the one-time code sent to ${getValues('email')}.`
              : 'We will email you a one-time code for this sign-in.'}
          </p>
          {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}</div>}
          <div className="login-fields" style={{ marginTop: errorMessage ? 15 : 0 }}>
            {!codeSent ? (
              <div>
                <label className="field-label" htmlFor="email">Email address</label>
                <input autoComplete="email" className="field-input" id="email" placeholder="you@school.edu" {...register('email')} />
                {errors.email && <div className="field-error">{errors.email.message}</div>}
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Sending code…' : 'Send sign-in code'} {!submitting && <ArrowRight size={16} />}
                </button>
              </div>
            ) : (
              <>
                <input aria-label="Email address" autoComplete="email" className="field-input" readOnly {...register('email')} />
                <div>
                  <label className="field-label" htmlFor="code">Six-digit code</label>
                  <input
                    autoComplete="one-time-code"
                    className="field-input"
                    id="code"
                    inputMode="numeric"
                    maxLength={6}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    value={code}
                  />
                </div>
                <button className="button button-primary login-submit" disabled={submitting} type="submit">
                  {submitting ? 'Verifying…' : 'Verify and sign in'} {!submitting && <ArrowRight size={16} />}
                </button>
                <button
                  className="text-link"
                  disabled={submitting || cooldown > 0}
                  onClick={() => void sendCode(getValues('email').trim().toLowerCase())}
                  type="button"
                >
                  {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
                </button>
                <button className="text-link" onClick={() => {
                  setCodeSent(false)
                  setCode('')
                  setErrorMessage('')
                }} type="button">Use a different email</button>
              </>
            )}
          </div>
          <div className="footer-note">
            Need an account? <Link className="text-link" to="/">Choose a registration type</Link>
          </div>
        </form>
      </section>
    </main>
  )
}
