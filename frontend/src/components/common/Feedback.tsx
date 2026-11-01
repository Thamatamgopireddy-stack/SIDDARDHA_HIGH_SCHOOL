import { AlertCircle, CheckCircle2, LoaderCircle } from 'lucide-react'
import { getApiError } from '../../lib/api'

export function LoadingState({ label = 'Loading data…' }: { label?: string }) {
  return <div className="loading-state"><LoaderCircle className="spinner" size={18} /> {label}</div>
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="error-state" role="alert">
      <AlertCircle size={20} style={{ margin: '0 auto 8px' }} />
      <div>{getApiError(error)}</div>
      {onRetry && <button className="button button-sm" onClick={onRetry} style={{ marginTop: 12 }} type="button">Try again</button>}
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><CheckCircle2 size={19} /></div>
      <strong style={{ color: '#52617a' }}>{title}</strong>
      {description && <div style={{ marginTop: 6 }}>{description}</div>}
    </div>
  )
}

export function Toast({ message, error = false }: { message: string; error?: boolean }) {
  return <div className={`toast${error ? ' toast-error' : ''}`} role={error ? 'alert' : 'status'}>{message}</div>
}
