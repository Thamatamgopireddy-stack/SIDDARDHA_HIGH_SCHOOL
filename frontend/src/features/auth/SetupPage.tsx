import { Settings2 } from 'lucide-react'
import { appConfig } from '../../lib/env'

export function SetupPage() {
  return (
    <main className="screen-center" style={{ padding: 20 }}>
      <section className="card" style={{ width: 'min(600px, 100%)', padding: 28 }}>
        <div className="empty-icon" style={{ marginLeft: 0 }}><Settings2 size={20} /></div>
        <div className="eyebrow">One-time setup</div>
        <h1 style={{ fontSize: 26 }}>Connect your school workspace</h1>
        <p className="subtitle" style={{ lineHeight: 1.8 }}>
          Add the public Supabase project URL, anon key, and backend API URL to <code>frontend/.env</code>, then restart the Vite server.
        </p>
        <div className="notice" style={{ marginTop: 18 }}>
          Required keys: <code>VITE_SUPABASE_URL</code>, <code>VITE_SUPABASE_ANON_KEY</code>, and <code>VITE_API_BASE_URL</code>.
          Only the public anon key belongs in frontend configuration. Never use a service-role key here.
        </div>
        <div className="footer-note">{appConfig.appName} · {appConfig.schoolName}</div>
      </section>
    </main>
  )
}
