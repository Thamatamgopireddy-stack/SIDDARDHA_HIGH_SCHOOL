import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Save, ShieldCheck, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { ErrorState, LoadingState, Toast } from '../../components/common/Feedback'
import { getApiError, getData, patchData } from '../../lib/api'
import type { Profile } from '../../lib/types'
import { Link } from 'react-router-dom'

const schema = z.object({
  display_name: z.string().trim().min(1, 'Display name is required').max(200),
  phone: z.union([z.string().max(32), z.literal('')]).optional(),
})
type Values = z.infer<typeof schema>

export function ProfilePage() {
  const [toast, setToast] = useState('')
  const client = useQueryClient()
  const profile = useQuery({ queryKey: ['profile'], queryFn: () => getData<Profile>('/auth/me') })
  const permissions = useQuery({ queryKey: ['permissions'], queryFn: () => getData<string[]>('/auth/permissions') })
  const form = useForm<Values>({ resolver: zodResolver(schema) })
  const update = useMutation({
    mutationFn: (values: Values) => patchData<Profile, { display_name: string; phone: string | null }>('/auth/profile', {
      display_name: values.display_name,
      phone: values.phone || null,
    }),
    onSuccess: async (value) => {
      client.setQueryData(['profile'], value)
      setToast('Profile updated.')
    },
  })

  useEffect(() => {
    if (profile.data) form.reset({ display_name: profile.data.display_name, phone: profile.data.phone ?? '' })
  }, [profile.data, form])

  if (profile.isLoading) return <LoadingState label="Loading your profile…" />
  if (profile.error || !profile.data) return <ErrorState error={profile.error ?? new Error('Profile unavailable')} onRetry={() => void profile.refetch()} />

  return (
    <>
      <div className="page-heading"><div><div className="eyebrow">Account</div><h1>My profile</h1><p className="subtitle">Your school identity and application access.</p></div></div>
      {update.error && <div className="notice notice-error" role="alert" style={{ marginBottom: 15 }}>{getApiError(update.error)}</div>}
      <section className="grid profile-grid">
        <article className="card profile-summary">
          <div className="profile-large-avatar">{initials(profile.data.display_name)}</div>
          <div className="card-title">{profile.data.display_name}</div>
          <div className="card-subtitle">{profile.data.email ?? 'No email on profile'}</div>
          <div className="inline-meta" style={{ justifyContent: 'center', gap: 6, marginTop: 16, color: '#27835d', fontSize: 11 }}><ShieldCheck size={14} /> Active school account</div>
        </article>
        <article className="card">
          <div className="card-header"><div><div className="card-title">Profile details</div><div className="card-subtitle">Update your name and contact phone</div></div><UserRound size={17} color="#8290a4" /></div>
          <div className="card-body">
            <form className="login-fields" onSubmit={(event) => void form.handleSubmit((values) => update.mutate(values))(event)}>
              <div><label className="field-label" htmlFor="profile-name">Display name</label><input className="field-input" id="profile-name" {...form.register('display_name')} />{form.formState.errors.display_name && <div className="field-error">{form.formState.errors.display_name.message}</div>}</div>
              <div><label className="field-label" htmlFor="profile-email">Email address</label><input className="field-input" id="profile-email" readOnly value={profile.data.email ?? ''} /><div className="card-subtitle" style={{ marginTop: 5 }}>Managed by Supabase Auth</div></div>
              <div><label className="field-label" htmlFor="profile-phone">Phone</label><input className="field-input" id="profile-phone" {...form.register('phone')} />{form.formState.errors.phone && <div className="field-error">{form.formState.errors.phone.message}</div>}</div>
              <div className="detail-list">
                <Detail label="School ID" value={profile.data.school_id} />
                <Detail label="Access permissions" value={permissions.data?.length.toString() ?? '—'} />
              </div>
              <button className="button button-primary" disabled={update.isPending} type="submit"><Save size={14} />{update.isPending ? 'Saving…' : 'Save profile'}</button>
              <Link className="button" to="/change-password">Change password</Link>
            </form>
          </div>
        </article>
      </section>
      {profile.data.must_change_password && <div className="notice" style={{ marginTop: 16 }}>Your account requires a password change. Use the Supabase password reset flow; this setting is managed by your school administrator.</div>}
      {toast && <Toast message={toast} />}
    </>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div><div className="meta-label">{label}</div><div className="meta-value">{value}</div></div>
}

function initials(name: string) {
  return name.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('')
}
