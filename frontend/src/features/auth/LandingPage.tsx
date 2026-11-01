import { ArrowRight, GraduationCap, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { appConfig } from '../../lib/env'

export function LandingPage() {
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
          <p>Secure tools for school leaders, teachers, and staff—all in one workspace.</p>
          <div className="login-feature"><ShieldCheck size={17} /> Every sign-in is verified by email code</div>
        </div>
        <div className="login-copy">© {new Date().getFullYear()} {appConfig.schoolName}</div>
      </section>
      <section className="login-form-panel">
        <div className="login-form">
          <div className="eyebrow">Get started</div>
          <h2>Welcome to {appConfig.appName}</h2>
          <p className="login-intro">Choose the option that matches your school role.</p>
          <div className="login-fields">
            <Link className="button button-primary login-submit" to="/login">
              Sign in with email code <ArrowRight size={16} />
            </Link>
            <Link className="button button-secondary login-submit" to="/register/admin">
              Request an administrator account
            </Link>
            <Link className="button button-secondary login-submit" to="/register/staff">
              Request a staff account
            </Link>
          </div>
          <div className="footer-note">Account requests are reviewed by the school Super Admin.</div>
          <div className="footer-note"><Link className="text-link" to="/owner-bootstrap">First-time owner setup</Link></div>
        </div>
      </section>
    </main>
  )
}
